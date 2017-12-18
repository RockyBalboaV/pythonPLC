# coding=utf-8

import time
import subprocess
import logging
from contextlib import contextmanager

from eventlet import monkey_patch, Timeout

from requests.exceptions import RequestException
from celery import Celery
from celery.five import monotonic
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy.orm.exc import UnmappedClassError

from models import eng, Base, YjPLCInfo, Value, Session
from data_collection import load_snap7
from utils.station_alarm import check_time_err, connect_server_err, server_return_err, db_commit_err, ntpdate_err
from utils.plc_alarm import connect_plc_err, read_err
from util import encryption_client, decryption_client
from param import (ID_NUM, BEAT_URL, CONNECT_TIMEOUT, REQUEST_TIMEOUT, CHECK_DELAY, SERVER_TIMEOUT, PLC_TIMEOUT,
                   START_TIMEDELTA, NTP_SERVER)
from utils.redis_middle_class import r
from utils.station_data import (redis_alarm_variables, beats_data, plc_info, redis_group_read_info,
                                redis_group_upload_info, redis_variable_info)
from utils.plc_connect import plc_client
from utils.mc import mc as cache
from utils.server_connect import upload, upload_data, get_config, req_s
from utils.plc_connect import read_multi

import snap7

snap7_client = list()

# 初始化celery
app = Celery(
    'test_celery'
)
app.config_from_object('celeryconfig', force=True)

monkey_patch(MySQLdb=True)

# 日志
logging.basicConfig(level=logging.WARN)
# logging.basicConfig(filename='logger.log', level=logging.INFO)
logging.getLogger(__name__).addHandler(logging.NullHandler())

# 读取snap7 C库
load_snap7()

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic() < timeout_at:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else.
            cache.delete(lock_id)


def database_reset():
    """
    初始化数据库
    
    :return: 
    """

    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


def boot():
    """
    开机初次运行
    
    :return: 
    """

    logging.debug('boot ruuning')

    Base.metadata.create_all(bind=eng)

    r.set('id_num', ID_NUM)


def before_running():
    """
    运行前设置
    
    :return: 
    """
    logging.debug('运行前初始化')

    # 清除上次运行数据
    r.set('group_upload', None)
    r.set('group_read', None)
    r.set('variable', None)
    r.set('alarm_info', None)
    r.set('check_time', None)
    r.set('plc', None)
    r.set('con_time', None)

    session = Session()
    try:
        # 设定服务开始运行时间
        current_time = int(time.time())
        start_time = current_time + START_TIMEDELTA

        # 设定报警信息
        redis_alarm_variables(r)

        # 获取该终端所有PLC信息
        plc_models = session.query(YjPLCInfo).all()

        # 缓存PLC信息
        plc_data = plc_info(r, plc_models)
        logging.info('PLC配置信息： ' + str(plc_data))

        global snap7_client
        snap7_client = list()

        for plc in plc_models:

            # 获得该PLC的信息
            ip = plc.ip
            rack = plc.rack
            slot = plc.slot

            # client = snap7.client.Client()
            #
            # try:
            #     logging.debug('plc连接尝试 ip:{} rack:{} slot:{}'.format(ip, rack, slot))
            #     client.connect(ip, rack, slot)
            # except Snap7Exception as e:
            #     logging.error('PLC无法连接，请查看PLC状态' + str(e))
            client = snap7.client.Client()
            client.connect(ip, rack, slot)
            snap7_client.append({'ip': ip, 'client': client})
            with plc_client(ip, rack, slot) as client:
                # print(client.get_connected())
                # 获取该PLC下所有组信息
                groups = plc.groups

                # 设定变量组信息
                for g in groups:
                    if g.is_upload:
                        redis_group_upload_info(r, g, start_time)
                    redis_group_read_info(r, g, start_time)
                    redis_variable_info(r, g)
                    # print(r.get('group_upload'))
                    # print(r.get('group_read'))
                    # print(r.get('variable'))

                    # 变量写入
                    # 获取该变量组下所有变量信息
                    # variables = g.variables

                    # if variables:
                    #     for v in variables:
                    #         plc_write(v, plc_cli, plc)

                    # client.disconnect()
                    # client.destroy()
        # 数据库写入操作后，关闭数据库连接
        session.commit()

    # except Exception as e:
    #     logging.exception('before_running' + str(e))
    #     session.rollback()
    finally:
        session.close()


@app.task(bind=True, ignore_result=True, default_retry_delay=10, max_retries=3, soft_time_limit=10)
def self_check(self):
    """
    celery任务
    定时自检
    
    :return: 
    """

    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            logging.debug('自检')

            current_time = int(time.time())

            session = Session()
            try:
                # 获取站点配置信息
                id_num = r.get('id_num')

                # 获取上次检查时间并检查时间间隔，判断程序运行状态
                check_time = r.get('check_time')
                if check_time:
                    check_time = int(check_time)
                    # logging.debug('上次检查时间：{}'.format(datetime.datetime.fromtimestamp(check_time)))
                    if current_time - check_time > CHECK_DELAY:
                        alarm = check_time_err(id_num)
                        session.add(alarm)
                r.set('check_time', current_time)

                # 检查与服务器通讯状态
                con_time = r.get('con_time')
                if con_time:
                    con_time = int(con_time)
                    # logging.debug('上次服务器通讯时间：{}'.format(datetime.datetime.fromtimestamp(con_time)))
                    if current_time - con_time > SERVER_TIMEOUT:
                        alarm = connect_server_err(id_num)
                        session.add(alarm)

                # 检查PLC通讯状态
                plcs = r.get('plc')
                if not plcs:
                    plc_models = session.query(YjPLCInfo)
                    plcs = plc_info(r, plc_models)
                    r.set('plc', plcs)

                for plc in plcs:
                    plc_connect_time = int(plc['time'])
                    # logging.debug('PLC连接时间：{}'.format(datetime.datetime.fromtimestamp(plc_connect_time)))

                    # 超过一定时间的上传服务器
                    if current_time - plc_connect_time > PLC_TIMEOUT:
                        alarm = connect_plc_err(
                            id_num,
                            plc_id=plc['id'],
                        )
                        session.add(alarm)

                # 数据库写入，关闭连接
                session.commit()
            # except Exception as e:
            #     logging.exception('self_check' + str(e))
            #     session.rollback()
            finally:
                session.close()


@app.task(bind=True, ignore_result=True, soft_time_limit=20)
def beats(self):
    """
    celery任务
    与服务器的心跳连接
    
    :param : 
    :return: 
    """
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            time1 = time.time()
            logging.debug('心跳连接')

            session = Session()
            try:

                current_time = int(time.time())

                # 从数据库获取站点信息
                id_num = ID_NUM

                # 获取上次心跳时间
                con_time = r.get('con_time')

                # 获取心跳时上传的数据
                data = beats_data(id_num, con_time, session, current_time)
                # print(data)
                data = encryption_client(data)

                # 发送心跳包
                try:
                    rv = req_s.post(BEAT_URL, data=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

                # 连接服务器失败
                except (RequestException, MaxRetriesExceededError) as e:
                    logging.warning('心跳连接错误：' + str(e))
                    log = connect_server_err(id_num)
                    session.add(log)

                # 连接成功
                else:
                    # data = decryption_client(rv.json())
                    # print(rv.status_code)
                    data = rv.json()
                    # print(data)

                    # 更新服务器通讯时间
                    r.set('con_time', current_time)

                    # 配置有更新
                    if data['is_modify'] == 1:
                        logging.info('发现配置有更新，准备获取配置')
                        get_config()
                        before_running()
                finally:
                    session.commit()

            # except Exception as e:
            #     logging.exception('beats' + str(e))
            #     session.rollback()
            finally:
                session.close()
                time2 = time.time()
                print('beats', time2 - time1)


@app.task(bind=True, ignore_result=True, soft_time_limit=10)
def check_upload(self):
    """
    检查变量组上传时间，将满足条件的变量组数据打包上传
    
    :return: 
    """
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            upload_time1 = time.time()
            logging.debug('检查变量组上传时间')
            # print('上传')

            current_time = int(time.time())

            session = Session()

            # 在redis中查询需要上传的变量组id
            group_upload_data = r.get('group_upload')

            # print(group_upload_data)

            for g in group_upload_data:
                if current_time >= g['upload_time']:
                    g['is_uploading'] = True
            r.set('group_upload', group_upload_data)
            try:

                group_id = []
                value_list = list()

                for g in group_upload_data:
                    if current_time >= g['upload_time']:
                        value_list += upload_data(g, current_time)
                        group_id.append(g['id'])
                        g['last_time'] = g['upload_time']
                        g['upload_time'] = current_time + g['upload_cycle']
                        g['is_uploading'] = False

                        # print('下次上传时间', datetime.datetime.fromtimestamp(g['upload_time']))

                # print(group_id)

                # print('上传数据', len(value_list), value_list)
                upload(value_list, group_id)

                # 设置为不在上传的状态
                # group_data = r.get('group_upload')
                # for g in group_data:
                #     if g['id'] in group_id:
                #         g['is_uploading'] = False
                r.set('group_upload', group_upload_data)

                # except Exception as e:
                #     logging.exception('check_group' + str(e))

                for g in group_upload_data:
                    if current_time >= g['upload_time']:
                        g['is_uploading'] = False
                r.set('group_upload', group_upload_data)

            finally:
                session.close()
                upload_time2 = time.time()
                print('上传时间', upload_time2 - upload_time1)


@app.task(bind=True, ignore_result=True, soft_time_limit=2)
def check_gather(self):
    """
    检查变量采集时间，采集满足条件的变量值

    :return: 
    """

    lock_id = '{0}-lock'.format(self.name)

    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            time1 = time.time()
            logging.debug('检查变量采集时间')

            current_time = int(time.time())

            session = Session()
            try:
                plcs = r.get('plc')
                # print(plc_client)

                group_read_data = r.get('group_read')

                # print(plcs)
                for plc in plcs:
                    # todo 循环内部 使用并发

                    group_id = []
                    for v in group_read_data:
                        if v['plc_id'] == plc['id'] and current_time >= v['read_time']:
                            group_id.append(v['id'])
                            v['read_time'] = current_time + v['read_cycle']
                    r.set('group_read', group_read_data)

                    group_data = r.get('variable')
                    variables = [variable
                                 for group in group_data if group['group_id'] in group_id
                                 for variable in group['variables']
                                 ]

                    # print(variables)
                    print('采集数量', len(variables))

                    # client = plc_connect(plc)
                    # with Timeout(3, False):
                    if True:
                        with plc_client(plc['ip'], plc['rack'], plc['slot']) as client:
                            if client.get_connected():
                                plc['time'] = current_time

                            if variables:

                                # readsuan(variables)
                                # variables = variables[0:2]
                                # print('variables', len(variables))

                                while len(variables) > 0:
                                    variable_group = variables[:18]
                                    variables = variables[18:]

                                    # print(len(variables))
                                    # print(plc)
                                    try:
                                        read_multi(
                                            plc=plc,
                                            variables=variable_group,
                                            current_time=current_time,
                                            client=client
                                        )
                                    except:
                                        print('跳过一次采集')

                                        # client.disconnect()
                                        # client.destroy()

                time2 = time.time()
                print('采集时间' + str(time2 - time1))
                r.set('plc', plcs)

            # except Exception as e:
            #     logging.excexcept Excepeption('check_var' + str(e))
            #     session.rollback()
            finally:
                session.close()


@app.task(bind=True, ignore_result=True, default_retry_delay=60, max_retries=3)
def ntpdate(self):
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            # 使用supervisor启动时用户为root 不需要sudo输入密码 不安全
            session = Session()
            try:
                pw = 'touhou'

                cmd2 = 'echo {} | sudo -S ntpdate {}'.format(pw, NTP_SERVER)
                ntp = subprocess.Popen(
                    cmd2,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                status = ntp.wait()
                stdout, stderr = ntp.communicate()

                if not status:  # 判断进程执行状态
                    note = '完成校时 :{}'.format(stdout.decode('utf-8'))
                    logging.info(note)
                else:
                    note = '校时失败 :{}'.format(stderr.decode('utf-8'))
                    logging.error(note)
                    id_num = r.get('id_num')
                    alarm = ntpdate_err(
                        id_num=id_num,
                        note=note
                    )
                    session.add(alarm)
                    session.commit()
            # except Exception as e:
            #     logging.exception('ntpdate' + str(e))
            #     session.rollback()
            finally:
                session.close()


@app.task(bind=True, ignore_result=True)
def db_clean(self):
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            # 删除一天前的采集数据
            current_time = int(time.time())
            session = Session()
            try:
                session.query(Value).filter(Value.time < current_time - 60 * 60 * 24).delete(synchronize_session=False)
                session.commit()
            finally:
                session.close()


@app.task(bind=True, ignore_result=True, soft_time_limit=10)
def check_alarm(self):
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            # r.set('alarm_info', None)
            logging.debug('check alarm')
            # print('检查报警')
            # redis_alarm_variables(r)

            is_no_alarm = r.get('is_no_alarm')
            if is_no_alarm:
                return
            alarm_variables = r.get('alarm_variables')
            # print('报警变量', alarm_variables)

            if not alarm_variables:
                redis_alarm_variables(r)
                return

            # 循环报警变量，查看最近采集的数值是否满足报警条件
            current_time = int(time.time())
            alarm_data = list()

            session = Session()
            try:

                for alarm in alarm_variables:
                    # 获取需要判断的采集数据
                    if alarm['delay']:
                        values = session.query(Value).filter_by(var_id=alarm['var_id']). \
                            filter(Value.time > current_time - alarm['delay'] - 1).all()
                    else:
                        values = session.query(Value).filter_by(var_id=alarm['var_id']). \
                            order_by(Value.time.desc()).limit(1).all()

                    is_alarm = False
                    if alarm['type'] == 1:
                        for v in values:
                            if bool(v.value) == bool(alarm['limit']):
                                is_alarm = True
                            else:
                                is_alarm = False
                                break

                    elif alarm['type'] == 2:
                        if alarm['symbol'] == 1:
                            for v in values:
                                if v.value > alarm['limit']:
                                    is_alarm = True
                                else:
                                    is_alarm = False
                                    break

                        elif alarm['symbol'] == 2:
                            for v in values:
                                if v.value >= alarm['limit']:
                                    is_alarm = True
                                else:
                                    is_alarm = False
                                    break

                        elif alarm['symbol'] == 3:
                            for v in values:
                                if v.value < alarm['limit']:
                                    is_alarm = True
                                else:
                                    is_alarm = False
                                    break

                        elif alarm['symbol'] == 4:
                            for v in values:
                                if v.value <= alarm['limit']:
                                    is_alarm = True
                                else:
                                    is_alarm = False
                                    break

                        elif alarm['symbol'] == 5:
                            for v in values:
                                if v.value == alarm['limit']:
                                    is_alarm = True
                                else:
                                    is_alarm = False
                                    break
                        else:
                            is_alarm = False

                    else:
                        is_alarm = False

                    if is_alarm and not alarm['is_alarming']:
                        alarm_data.append({
                            'i': alarm['var_id'],
                            'a': is_alarm
                        })
                        alarm['is_alarming'] = True
                    elif not is_alarm and alarm['is_alarming']:
                        alarm_data.append({
                            'i': alarm['var_id'],
                            'a': is_alarm
                        })
                        alarm['is_alarming'] = False

                r.set('alarm_variables', alarm_variables)

                if alarm_data:
                    alarm_info = {'time': current_time, 'data': alarm_data}
                    old_alarm = r.get('alarm_info')
                    # print(old_alarm)
                    if old_alarm:
                        old_alarm.append(alarm_info)
                        r.set('alarm_info', old_alarm)
                    else:
                        r.set('alarm_info', [alarm_info])

                        # print(alarm_info)
                        # print(alarm_variables)
            # except Exception as e:
            #     logging.exception('check_alarm' + str(e))
            #     session.rollback()
            finally:
                session.close()

            return
