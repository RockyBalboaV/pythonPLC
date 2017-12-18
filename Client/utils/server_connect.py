import logging
import time
import json

from requests import Session as ReqSession
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from sqlalchemy.exc import IntegrityError

from models import (Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, VarGroups, AlarmInfo, Value,
                    value_serialize)
from param import UPLOAD_URL, REQUEST_TIMEOUT, CONNECT_TIMEOUT, CONFIG_URL, CONFIRM_CONFIG_URL, MAX_RETRIES
from utils.station_func import decryption_client, encryption_client
from utils.redis_middle_class import r
from utils.station_alarm import connect_server_err, db_commit_err, server_return_err

# 初始化requests
req_s = ReqSession()
req_s.mount('http://', HTTPAdapter(max_retries=MAX_RETRIES))
req_s.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES))


def get_config():
    """
    连接服务器接口，获取本机变量信息

    :return: 
    """
    time1 = int(time.time())
    logging.debug('连接服务器,获取数据')

    session = Session()
    try:

        current_time = time.time()

        # 获取本机信息
        id_num = r.get('id_num')

        post_data = {
            'id_num': id_num
        }
        post_data = json.dumps(post_data)
        # logging.info('获取配置，发送请求：' + str(post_data))

        # 连接服务器
        try:
            time_c1 = time.time()
            rv = req_s.post(CONFIG_URL, data=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
            time_c2 = time.time()
            print('连接服务器获取配置', time_c2 - time_c1)
        # 连接失败
        except RequestException as e:
            logging.warning('获取配置错误：' + str(e))

            log = connect_server_err(id_num)
            session.add(log)

            # try:
            #     raise self.retry(exc=e)
            # except RequestException:
            #     pass
            # return 1
        # 连接成功
        else:
            # 记录本次服务器通讯时间
            r.set('con_time', current_time)

            if rv.status_code == 200:
                rp = rv.json()

                # data = rp['data']
                data = decryption_client(rp['data'])

                # print(data)

                # 配置更新，删除现有表
                time11 = time.time()
                try:
                    session.query(VarGroups).delete()
                    session.query(AlarmInfo).delete()
                    session.query(YjVariableInfo).delete()
                    session.query(YjStationInfo).delete()
                    session.query(YjPLCInfo).delete()
                    session.query(YjGroupInfo).delete()

                except IntegrityError as e:
                    logging.error('更新配置时，删除旧表出错: ' + str(e))
                    session.rollback()
                    alarm = db_commit_err(id_num, 'get_config')
                    session.add(alarm)
                else:
                    session.flush()

                # 添加'sqlalchemy' class数据
                session.bulk_insert_mappings(YjStationInfo, [data['stations']])
                session.bulk_insert_mappings(YjPLCInfo, data['plcs'])
                session.bulk_insert_mappings(YjGroupInfo, data['groups'])
                session.bulk_insert_mappings(YjVariableInfo, data['variables'])
                session.bulk_insert_mappings(VarGroups, data['variables_groups'])
                session.bulk_insert_mappings(AlarmInfo, data['alarm'])

                time12 = time.time()
                print('清空添加配置', time12 - time11)

                logging.debug('发送配置完成确认信息')
                time21 = time.time()
                result = server_confirm(CONFIRM_CONFIG_URL)
                time22 = time.time()
                print('确认配置获取', time22 - time21)

                if result:
                    logging.info('配置获取完成')
                else:
                    logging.error('无法向服务器确认获取配置已完成')

            else:
                log = server_return_err(id_num, 'get_config')
                session.add(log)
        finally:
            session.commit()

    # except Exception as e:
    #     logging.exception('get_config' + str(e))
    #     session.rollback()
    finally:
        session.close()
        time2 = time.time()
        print('get_config', time2 - time1)


def upload_data(group, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值

    :param group: 上传组参数字典
    :param current_time: 当前时间
    :return: 变量值列表
    """

    logging.debug('上传数据打包')

    value_list = list()

    session = Session()
    try:
        # 获取该组信息
        # print(group)
        server_record_cycle = group['server_record_cycle']

        # 准备本次上传的数据
        variables = group['var_id']

        for variable in variables:

            # 获取上次传输时间,没有上次时间就往前推一个上传周期
            if group['last_time'] is not None:
                get_time = group['last_time']
            else:
                get_time = current_time - group['upload_cycle']

            time1 = time.time()
            # 读取需要上传的值,所有时间大于上次上传的值
            all_values = session.query(Value).filter_by(var_id=variable).filter(
                get_time <= Value.time).filter(Value.time < current_time)

            # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
            while get_time < current_time:
                upload_value = all_values.filter(
                    get_time + server_record_cycle > Value.time).filter(Value.time >= get_time).order_by(
                    Value.time.desc()).first()
                # print('get_time', get_time)
                # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
                if upload_value:
                    # print('数据时间', upload_value.time)
                    value_dict = value_serialize(upload_value)
                    value_list.append(value_dict)

                get_time += server_record_cycle

            time2 = time.time()
            # print('采样时间', time2 - time1)
        # print(value_list)
        session.commit()
    # except Exception as e:
    #     logging.exception('upload_data' + str(e))
    #     session.rollback()
    finally:
        session.close()

    return value_list


def upload(variable_list, group_id):
    """
    数据上传
    :param variable_list: 
    :param group_id: 
    :return: 
    """

    logging.debug('上传数据')

    session = Session()
    try:
        # 获取本机信息
        id_num = r.get('id_num')

        # 包装数据
        data = {
            'id_num': id_num,
            'value': variable_list
        }

        # print('上传数据数量', len(data['value']))

        data = encryption_client(data)

        # 上传日志记录
        # logging.info('group_id: {}将要上传.'.format(group_id))

        # 连接服务器，准备上传数据
        try:
            rv = req_s.post(UPLOAD_URL, data=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
        except RequestException as e:
            logging.warning('上传数据错误：' + str(e))

            alarm = connect_server_err(id_num)
            session.add(alarm)

        else:
            # 日志记录
            # 正常传输
            if rv.status_code == 200:
                logging.info('group_id: {}成功上传.'.format(group_id))

            # 未知错误
            else:
                logging.error('upload无法识别服务端反馈 group_id: {}'.format(group_id))
                log = server_return_err(id_num, 'upload group_id: {}'.format(group_id))
                session.add(log)

        session.commit()

    # except Exception as e:
    #     logging.exception('upload' + str(e))
    #     session.rollback()
    finally:
        session.close()


def server_confirm(url):
    """
    发送请求后，收到服务器回执的确认

    :param url: 具体确认某个功能的地址
    :return: 
    """

    id_num = r.get('id_num')
    post_data = {
        'id_num': id_num
    }

    post_data = json.dumps(post_data)
    session = Session()
    print(post_data)
    try:
        rp = req_s.post(url, data=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except RequestException as e:
        logging.warning('确认请求发送失败: ' + str(e))
        alarm = connect_server_err(id_num, str(url))
        try:
            session.add(alarm)
            session.commit()
        # except Exception as e:
        #     logging.exception('server_confirm' + str(e))
        #     session.rollback()
        finally:
            session.close()
        return False
    else:
        http_code = rp.status_code
        if http_code == 200:
            return True
        else:
            return False
