# coding=utf-8

import time
import subprocess
import logging
import json
import pickle

from pymysql import connect
from requests.exceptions import RequestException
from celery import Celery
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

from models import YjPLCInfo, Value, Session
from utils.station_alarm import check_time_err, connect_server_err, server_return_err, db_commit_err, ntpdate_err
from utils.plc_alarm import connect_plc_err, read_err, Snap7ConnectException, Snap7ReadException
from param import (ID_NUM, BEAT_URL, CONNECT_TIMEOUT, REQUEST_TIMEOUT, CHECK_DELAY, SERVER_TIMEOUT, PLC_TIMEOUT,
                   NTP_SERVER)
from utils.mc import memcache_lock
from utils.redis_middle_class import r
from utils.station_data import (redis_alarm_variables, beats_data, plc_info)
from utils.plc_connect import plc_client
from utils.server_connect import upload, upload_data, get_config, req_s, upload_data_redis
from utils.station_func import before_running, encryption_client, decryption_client
from utils.plc_connect import read_multi
from utils.mysql_middle import ConnMySQL

# 初始化celery
app = Celery(
    'test_celery'
)
app.config_from_object('celeryconfig', force=True)

# 日志
logging.basicConfig(level=logging.WARN)
logging.getLogger(__name__).addHandler(logging.NullHandler())


@app.task(bind=True, ignore_result=True, default_retry_delay=10, max_retries=3, time_limit=10)
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
    lock_time1 = time.time()
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        print('lock', acquired)
        if acquired:
            lock_time2 = time.time()
            print('lock_time', lock_time2 - lock_time1)
            upload_time1 = time.time()
            logging.debug('检查变量组上传时间')
            # print('上传')

            current_time = int(time.time())


            # 在redis中查询需要上传的变量组id
            group_upload_data = r.get('group_upload')

            # print(group_upload_data)

            for g in group_upload_data:
                if current_time >= g['upload_time']:
                    g['is_uploading'] = True
            r.set('group_upload', group_upload_data)

            group_id = []
            value_list = list()

            dtime1 = time.time()
            for g in group_upload_data:
                if current_time >= g['upload_time']:
                    value_list += upload_data(g, current_time)
                    group_id.append(g['id'])
                    g['last_time'] = g['upload_time']
                    g['upload_time'] = current_time + g['upload_cycle']
                    # 设置为不在上传的状态
                    g['is_uploading'] = False

                    # print('下次上传时间', datetime.datetime.fromtimestamp(g['upload_time']))
            dtime2 = time.time()
            print('data', dtime2 - dtime1)
            # print(group_id)

            # print('上传数据', len(value_list), value_list)
            utime1 = time.time()
            upload(value_list, group_id)
            utime2 = time.time()
            print('upload', utime2 - utime1)

            r.set('group_upload', group_upload_data)

            # except Exception as e:
            #     logging.exception('check_group' + str(e))

            upload_time2 = time.time()
            print('上传时间', upload_time2 - upload_time1)


@app.task(bind=True, ignore_result=True, soft_time_limit=2)
def check_gather_redis(self):
    """
    检查变量采集时间，采集满足条件的变量值

    :return: 
    """
    lock_time1 = time.time()
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:

            with ConnMySQL() as db:
                cur = db.cursor()
                lock_time2 = time.time()
                print('lock_time', lock_time2 - lock_time1)
                time1 = time.time()
                logging.debug('检查变量采集时间')

                current_time = int(time.time())
                value_list = list()
                session = Session()
                try:
                    plcs = r.get('plc')

                    group_read_data = r.get('group_read')

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
                                        value_info = read_multi(
                                            plc=plc,
                                            variables=variable_group,
                                            current_time=current_time,
                                            client=client
                                        )
                                    except SoftTimeLimitExceeded:
                                        raise
                                    except Snap7ReadException as e:
                                        id_num = r.get('id_num')
                                        area, db_num, addr, data_type = e.args
                                        alarm = read_err(
                                            id_num=id_num,
                                            plc_id=plc['id'],
                                            plc_name=plc['name'],
                                            area=area,
                                            db_num=db_num,
                                            address=addr,
                                            data_type=data_type
                                        )
                                        session.add(alarm)

                                    else:
                                        value_list += value_info

                                        # except Exception:
                                        #     print('跳过一次采集')

                                        # client.disconnect()
                                        # client.destroy()
                    # session.bulk_insert_mappings(Value, value_list)
                    # session.commit()
                    ctime1 = time.time()
                    # value_insert_sql = "insert into `values`(var_id, value, time) values "
                    # if value_list:
                    #     v = map(str, value_list)
                    #
                    #     value_insert_sql = value_insert_sql + ','.join(v)
                    #
                    #     cur.execute(value_insert_sql)
                    #     db.commit()
                    redis_value = r.conn.hlen('value')
                    print(redis_value)

                    # value_data = {str(current_time): value_list}
                    value_list = pickle.dumps(value_list)
                    # if redis_value:
                    r.conn.hset('value', str(current_time), value_list)
                    # else:
                    #     r.set('value', value_data)

                    ctime2 = time.time()
                    print('commit', ctime2 - ctime1)


                    r.set('plc', plcs)
                # except Exception as e:
                #     logging.excexcept Excepeption('check_var' + str(e))
                #     session.rollback()
                finally:
                    time2 = time.time()
                    print('采集时间' + str(time2 - time1))

                    cur.close()
                    # session.close()


@app.task(bind=True, ignore_result=True, soft_time_limit=2)
def check_gather(self):
    """
    检查变量采集时间，采集满足条件的变量值

    :return:
    """
    lock_time1 = time.time()
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:

            with ConnMySQL() as db:
                cur = db.cursor()
                lock_time2 = time.time()
                # print('lock_time', lock_time2 - lock_time1)
                time1 = time.time()
                logging.debug('检查变量采集时间')

                current_time = int(time.time())
                value_list = list()
                session = Session()
                try:
                    plcs = r.get('plc')

                    group_read_data = r.get('group_read')

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
                        # print('采集数量', len(variables))

                        # client = plc_connect(plc)
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
                                        value_info = read_multi(
                                            plc=plc,
                                            variables=variable_group,
                                            current_time=current_time,
                                            client=client
                                        )
                                    except SoftTimeLimitExceeded:
                                        raise
                                    except Snap7ReadException as e:
                                        id_num = r.get('id_num')
                                        area, db_num, addr, data_type = e.args
                                        alarm = read_err(
                                            id_num=id_num,
                                            plc_id=plc['id'],
                                            plc_name=plc['name'],
                                            area=area,
                                            db_num=db_num,
                                            address=addr,
                                            data_type=data_type
                                        )
                                        session.add(alarm)

                                    else:
                                        value_list += value_info

                                        # except Exception:
                                        #     print('跳过一次采集')

                                        # client.disconnect()
                                        # client.destroy()
                    # session.bulk_insert_mappings(Value, value_list)
                    # session.commit()
                    ctime1 = time.time()
                    value_insert_sql = "insert into `values`(var_id, value, time) values "
                    if value_list:
                        v = map(str, value_list)

                        value_insert_sql = value_insert_sql + ','.join(v)

                        cur.execute(value_insert_sql)
                        db.commit()

                    # value_data = {str(current_time): value_list}
                    # if redis_value:
                    # else:
                    #     r.set('value', value_data)

                    ctime2 = time.time()
                    # print('commit', ctime2 - ctime1)


                    r.set('plc', plcs)
                # except Exception as e:
                #     logging.excexcept Excepeption('check_var' + str(e))
                #     session.rollback()
                finally:
                    time2 = time.time()
                    # print('采集时间' + str(time2 - time1))

                    cur.close()
                    # session.close()


@app.task(bind=True, ignore_result=True, default_retry_delay=60, max_retries=3)
def ntpdate(self):
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            # 使用supervisor启动时用户为root 不需要sudo输入密码 不安全
            session = Session()
            try:
                pw = 'touhou'

                cmd2 = 'echo {0} | sudo -S ntpdate {1}'.format(pw, NTP_SERVER)
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
                    note = '完成校时 :{0}'.format(stdout.decode('utf-8'))
                    logging.info(note)
                else:
                    note = '校时失败 :{0}'.format(stderr.decode('utf-8'))
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


@app.task(bind=True, ignore_result=True, time_limit=10)
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
