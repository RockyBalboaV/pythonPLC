import logging
import time
import json
import pickle

from requests import Session as ReqSession
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from sqlalchemy.exc import IntegrityError
from pymysql import connect, Error

from models import Session, Value
from param import UPLOAD_URL, REQUEST_TIMEOUT, CONNECT_TIMEOUT, CONFIG_URL, CONFIRM_CONFIG_URL, MAX_RETRIES
from utils.station_func import decryption_client, encryption_client
from utils.redis_middle_class import r
from utils.station_alarm import connect_server_err, db_commit_err, server_return_err
from utils.mysql_middle import ConnMySQL

# 初始化requests
req_s = ReqSession()
req_s.mount('http://', HTTPAdapter(max_retries=MAX_RETRIES))
req_s.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES))


def get_config():
    """
    连接服务器接口，获取本机变量信息

    :return: 
    """
    gtime1 = int(time.time())
    logging.debug('连接服务器,获取数据')

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

        connect_server_err(id_num)

    # 连接成功
    else:
        # 记录本次服务器通讯时间
        r.set('con_time', current_time)

        if rv.status_code == 200:
            rp = rv.json()

            # data = rp['data']
            data = decryption_client(rp['data'])

            # print(data)
            time11 = time.time()

            with ConnMySQL() as db:
                cur = db.cursor()
                try:
                    # 配置更新，清空现有表
                    cur.execute('SET foreign_key_checks = 0')
                    cur.execute('truncate table `variables_groups`')
                    cur.execute('truncate table alarm_info')
                    # cur.execute('truncate table `values`')
                    cur.execute('truncate table yjvariableinfo')
                    cur.execute('truncate table yjgroupinfo')
                    cur.execute('truncate table yjplcinfo')
                    cur.execute('truncate table yjstationinfo')
                    cur.execute('SET foreign_key_checks = 1')
                    # 添加新获取的数据
                    station_sql = '''insert into `yjstationinfo`
                                                            (id, station_name, mac, ip, note, id_num, plc_count, ten_id, item_id)
                                                            values (%(id)s, %(station_name)s, %(mac)s, %(ip)s, %(note)s, %(id_num)s,
                                                            %(plc_count)s, %(ten_id)s, %(item_id)s)'''
                    cur.execute(station_sql, data['stations'])
                    plc_sql = '''insert into `yjplcinfo`(
                                                          id, station_id, plc_name, note, ip, mpi, type, plc_type, ten_id,
                                                           item_id, rack, slot, tcp_port) 
                                                          values (%(id)s, %(station_id)s, %(plc_name)s, %(note)s, %(ip)s, %(mpi)s, %(type)s,
                                                           %(plc_type)s, %(ten_id)s, %(item_id)s, %(rack)s, %(slot)s, %(tcp_port)s)'''
                    cur.executemany(plc_sql, data['plcs'])
                    group_sql = '''insert into `yjgroupinfo`(
                                                            id, group_name, note, upload_cycle, acquisition_cycle, server_record_cycle,
                                                             is_upload, ten_id, item_id, plc_id) 
                                                             values (%(id)s, %(group_name)s, %(note)s, %(upload_cycle)s,
                                                              %(acquisition_cycle)s, %(server_record_cycle)s, %(is_upload)s, %(ten_id)s,
                                                               %(item_id)s, %(plc_id)s)'''
                    cur.executemany(group_sql, data['groups'])
                    var_sql = '''insert into `yjvariableinfo`
                                 (id, variable_name, note, db_num, address, data_type, rw_type, ten_id, item_id,
                                  write_value, area, is_analog, analog_low_range, analog_high_range,
                                   digital_low_range, digital_high_range) 
                                   values (%(id)s, %(variable_name)s, %(note)s, %(db_num)s, %(address)s,
                                    %(data_type)s, %(rw_type)s, %(ten_id)s, %(item_id)s, %(write_value)s, %(area)s,
                                     %(is_analog)s, %(analog_low_range)s, %(analog_high_range)s,
                                      %(digital_low_range)s, %(digital_high_range)s)'''
                    cur.executemany(var_sql, data['variables'])
                    relation_sql = '''insert into `variables_groups`(id, variable_id, group_id) 
                                                              values (%(id)s, %(variable_id)s, %(group_id)s)'''
                    cur.executemany(relation_sql, data['variables_groups'])
                    alarm_sql = '''insert into `alarm_info`
                                   (id, variable_id, alarm_type, note, type, symbol, `limit`, delay) 
                                   values (%(id)s, %(variable_id)s, %(alarm_type)s, %(note)s, %(type)s, %(symbol)s,
                                    %(limit)s, %(delay)s)'''
                    cur.executemany(alarm_sql, data['alarm'])
                except Error as e:
                    logging.error('更新配置出错: ' + str(e))
                    db.rollback()
                    db_commit_err(id_num, 'get_config')
                else:
                    db.commit()
                finally:
                    cur.close()
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
            server_return_err(id_num, 'get_config')

        gtime2 = time.time()
        print('get_config', gtime2 - gtime1)


def key_filter(str_time, get_time):
    return int(str_time) >= int(get_time)


def upload_data_redis(group, current_time):
    time1 = time.time()

    logging.debug('上传数据打包')

    # 获取该组信息
    server_record_cycle = group['server_record_cycle']
    # 上传的组
    variables = tuple(group['var_id'])
    # 获取上次传输时间,没有上次时间就往前推一个上传周期
    if group['last_time'] is not None:
        get_time = group['last_time']
    else:
        get_time = current_time - group['upload_cycle']

    # 保存数据的空列表
    value_list = list()
    # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
    value_time = r.conn.hkeys('value')
    value_time = (str_time for str_time in value_time if int(str_time) >= int(get_time))
    while get_time < current_time:
        next_time = get_time + server_record_cycle
        for str_time in value_time:
            int_time = int(str_time)
            value_info = list()
            if next_time > int_time >= get_time:
                value = pickle.loads(r.conn.hget('value', str_time))
                for v in value:
                    if v[0] in variables:
                        value_info.append(v)
                value_list.append({'time': int_time, 'value': value_info})
                break
        get_time = next_time
    print(value_list)
    time2 = time.time()
    print('采样时间 2', time2 - time1)

    return value_list


def upload_data_orm(group, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值

    :param group: 上传组参数字典
    :param current_time: 当前时间
    :return: 变量值列表
    """
    time1 = time.time()

    logging.debug('上传数据打包')

    # 获取该组信息
    server_record_cycle = group['server_record_cycle']
    session = Session()
    try:
        # 上传的组
        variables = group['var_id']
        # 获取上次传输时间,没有上次时间就往前推一个上传周期
        if group['last_time'] is not None:
            get_time = group['last_time']
        else:
            get_time = current_time - group['upload_cycle']

        # 保存数据的空列表
        value_list = list()

        for variable in variables:
            # 读取需要上传的值,所有时间大于上次上传的值
            all_values = session.query(Value).filter_by(var_id=variable).filter(
                get_time <= Value.time).filter(Value.time < current_time)

            start_time = get_time
            # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
            while start_time < current_time:
                upload_value = all_values.filter(
                    start_time + server_record_cycle > Value.time).filter(Value.time >= start_time).order_by(
                    Value.time.desc()).first()

                next_time = start_time + server_record_cycle
                # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
                # todo 一次查询时间只存一份
                if upload_value:
                    value_info = {'i': upload_value.id, 'v': upload_value.value, 't': upload_value.time}
                    value_list.append(value_info)

                start_time = next_time
    finally:
        session.close()
        time2 = time.time()
        print('采样时间 2', time2 - time1)

    return value_list


def upload_data(group, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值

    :param group: 上传组参数字典
    :param current_time: 当前时间
    :return: 变量值列表
    """
    time1 = time.time()

    logging.debug('上传数据打包')

    # 获取该组信息
    server_record_cycle = group['server_record_cycle']

    # 上传的组
    variables = group['var_id']
    # 获取上次传输时间,没有上次时间就往前推一个上传周期
    if group['last_time'] is not None:
        get_time = group['last_time']
    else:
        get_time = current_time - group['upload_cycle']

    # 保存数据的空列表
    value_list = list()
    time_list = list()
    # 获取时间分段节点
    while current_time >= get_time:
        time_list.append(get_time)
        get_time += server_record_cycle

    # print(value_list, time_list)
    with ConnMySQL() as db:
        cur = db.cursor()
        try:
            for variable in variables:
                i = 0
                start_time = time_list[i]
                # 取出该变量在上次上传后采集的数值
                sql = '''select var_id, value, time from `values` where var_id = %s and %s > time and time >= %s'''
                cur.execute(sql, (int(variable), current_time, start_time))
                upload_value_list = cur.fetchall()
                # print(upload_value_list)
                for v in upload_value_list:
                    if v[2] >= start_time:
                        value_info = (v[0], v[1], v[2])
                        value_list.append(value_info)
                        i += 1
                        if i == len(time_list):
                            break
                        start_time = time_list[i]
        finally:
            cur.close()
    time2 = time.time()
    # print('采样时间 2', time2 - time1)
    # print(value_list)
    return value_list


def upload_data_new(group, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值

    :param group: 上传组参数字典
    :param current_time: 当前时间
    :return: 变量值列表
    """
    time1 = time.time()

    logging.debug('上传数据打包')

    # 获取该组信息
    server_record_cycle = group['server_record_cycle']

    # 上传的组
    variables = group['var_id']
    # 获取上次传输时间,没有上次时间就往前推一个上传周期
    if group['last_time'] is not None:
        get_time = group['last_time']
    else:
        get_time = current_time - group['upload_cycle']

    # 保存数据的空列表
    value_dict = dict()
    time_list = list()
    # 获取时间分段节点
    while current_time >= get_time:
        time_list.append(get_time)
        value_dict[str(get_time)] = list()
        get_time += server_record_cycle

    print(value_dict, time_list)
    with ConnMySQL() as db:
        cur = db.cursor()
        try:
            for variable in variables:
                i = 0
                start_time = time_list[i]
                # 取出该变量在上次上传后采集的数值
                sql = '''select var_id, value, time from `values` where var_id = %s and %s > time and time >= %s'''
                cur.execute(sql, (int(variable), current_time, start_time))
                upload_value_list = cur.fetchall()
                print(upload_value_list)
                for v in upload_value_list:
                    if v[2] >= start_time:
                        value_info = (v[0], v[1])
                        value_dict[str(start_time)].append(value_info)
                        i += 1
                        if i == len(time_list):
                            break
                        start_time = time_list[i]
        finally:
            cur.close()
    time2 = time.time()
    print('采样时间 2', time2 - time1)
    print(value_dict)
    return value_dict


def upload(variable_list, group_id):
    """
    数据上传
    :param variable_list: 
    :param group_id: 
    :return: 
    """

    logging.debug('上传数据')

    # 获取本机信息
    id_num = r.get('id_num')

    # 包装数据
    data = {
        'id_num': id_num,
        'value': variable_list
    }
    # print('upload_value', variable_list)
    # print('upload_len', len(variable_list))
    # print('上传数据数量', len(data['value']))

    data = encryption_client(data)

    # 上传日志记录
    # logging.info('group_id: {}将要上传.'.format(group_id))

    # 连接服务器，准备上传数据
    try:
        rv = req_s.post(UPLOAD_URL, data=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except RequestException as e:
        logging.warning('上传数据错误：' + str(e))

        connect_server_err(id_num)

    else:
        # 日志记录
        # 正常传输
        if rv.status_code == 200:
            logging.info('group_id: {}成功上传.'.format(group_id))

        # 未知错误
        else:
            logging.error('upload无法识别服务端反馈 group_id: {}'.format(group_id))
            server_return_err(id_num, 'upload group_id: {}'.format(group_id))


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
    # print(post_data)
    try:
        rp = req_s.post(url, data=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except RequestException as e:
        logging.warning('确认请求发送失败: ' + str(e))
        connect_server_err(id_num, str(url))
        return False
    else:
        http_code = rp.status_code
        if http_code == 200:
            return True
        else:
            return False
