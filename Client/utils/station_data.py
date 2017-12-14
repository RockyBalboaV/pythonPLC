import psutil
import time
import platform

from utils.redis_middle_class import ConnDB
from models import serialize, session, StationAlarm, PLCAlarm, AlarmInfo


def beats_data(id_num, con_time, current_time):
    """
    
    :param id_num: 
    :param con_time: 
    :param current_time: 
    :return: data = {
        'id_num': id_num,
        'station_alarms': station_alarms,
        'plc_alarms': plc_alarms,
        'station_info': info,
        'data_alarms': alarm_data
    }
    """
    r = ConnDB()
    # 获取心跳间隔时间内产生的报警
    alarm_data = r.get('alarm_info')
    r.set('alarm_info', None)
    # print(alarm_data)

    # 获取
    station_alarms = list()
    plc_alarms = list()
    if con_time:
        station = session.query(StationAlarm).filter(con_time <= StationAlarm.time). \
            filter(StationAlarm.time < current_time).all()
        for s in station:
            station_alarms.append(serialize(s))

        plc = session.query(PLCAlarm). \
            filter(con_time <= PLCAlarm.time).filter(PLCAlarm.time < current_time).all()
        for p in plc:
            plc_alarms.append(serialize(p))

    # 获取设备信息
    info = station_info()

    data = {
        'id_num': id_num,
        's_a': station_alarms,
        'p_a': plc_alarms,
        'info': info,
        'd_a': alarm_data
    }

    return data


def station_info():
    """
    
    :return:  dict = {
        'boot_time': boot_time,
        'total_usage': total_usage,
        'free_usage': free_usage,
        'total_memory': total_memory,
        'free_memory': free_memory,
        'bytes_sent': bytes_sent,
        'bytes_recv': bytes_recv,
        'cpu_percent': cpu_percent,
        'usage_percent': usage_percent,
        'memory_percent': memory_percent
    }

    """
    # 开机时间
    boot_time = int(psutil.boot_time())

    dist_info = psutil.disk_usage('/')
    # 硬盘总量
    total_usage = int(dist_info[0] / 1024 / 1024)
    # 空闲容量
    free_usage = int(dist_info[2] / 1024 / 1024)
    # 使用容量百分比
    usage_percent = dist_info[3]

    memory_info = psutil.virtual_memory()
    # 内存总量
    total_memory = int(memory_info[0] / 1024 / 1024)
    # 空闲内存
    free_memory = int(memory_info[4] / 1024 / 1024)
    # 使用内存百分比
    memory_percent = memory_info[2]

    # 只记录wifi流量，不记录通过有线连接的流量
    node_name = platform.node()
    if node_name == 'raspberrypi':
        net_info = psutil.net_io_counters(pernic=True, nowrap=True)['wlan0']
    elif node_name == 'MacBook-Pro.local':
        net_info = psutil.net_io_counters(pernic=True, nowrap=True)['en0']
    else:
        net_info = psutil.net_io_counters(nowrap=True)
    # 发送流量
    bytes_sent = int(net_info[0] / 1024 / 1024)
    # 接收流量
    bytes_recv = int(net_info[1] / 1024 / 1024)

    # cpu占用
    cpu_percent = psutil.cpu_percent()

    info = {
        'b_t': boot_time,
        't_u': total_usage,
        'f_u': free_usage,
        't_m': total_memory,
        'f_m': free_memory,
        'b_s': bytes_sent,
        'b_r': bytes_recv,
        'c_p': cpu_percent,
        'u_p': usage_percent,
        'm_p': memory_percent
    }

    return info


def plc_info(r, plcs):
    """
    连接plc，将连接实例存入list
    
    :param r: redis连接
    :param plcs: sqlalchemy数据库查询对象列表
    :return: snap7 client实例元组 [0]plc ip地址 [1]plc 机架号  [2]plc 插槽号 [3]plc 配置数据主键 [4]plc 名称 [5]plc 连接时间
    """
    current_time = int(time.time())
    plc_client = [
        {
            'id': plc.id,
            'ip': plc.ip,
            'rack': plc.rack,
            'slot': plc.slot,
            'name': plc.plc_name,
            'time': current_time
        }
        for plc in plcs
    ]
    r.set('plc', plc_client)

    return plc_client


def redis_alarm_variables(r):
    # session = Session()
    alarm_models = session.query(AlarmInfo).all()
    if alarm_models:
        data = [
            {
                'var_id': model.variable_id,
                'type': model.type,
                'symbol': model.symbol,
                'limit': model.limit,
                'delay': model.delay,
                'is_alarming': False
            }
            for model in alarm_models
        ]

        r.set('alarm_variables', data)
        r.set('is_no_alarm', False)
    else:
        r.set('is_no_alarm', True)

    return True


def redis_group_upload_info(r, g, start_time):
    # 变量组参数
    upload_cycle = g.upload_cycle if isinstance(g.upload_cycle, int) else 30
    plc_id = g.plc_id
    var_id = [model.variable.id for model in g.variables]
    group_id = g.id
    server_record_cycle = g.server_record_cycle
    group_name = g.group_name

    # 设定变量组初始上传时间,
    group_upload_info = {
        'id': group_id,
        'plc_id': plc_id,
        'upload_time': start_time + upload_cycle,
        'last_time': None,
        'is_uploading': False,
        'upload_cycle': upload_cycle,
        'server_record_cycle': server_record_cycle,
        'var_id': var_id,
        'group_name': group_name
    }
    group_upload_data = r.get('group_upload')
    if isinstance(group_upload_data, list):
        group_upload_data.append(group_upload_info)
    else:
        group_upload_data = [group_upload_info]
    r.set('group_upload', group_upload_data)


def redis_group_read_info(r, g, start_time):
    # 变量组参数
    acquisition_cycle = g.acquisition_cycle if isinstance(g.acquisition_cycle, int) else 30
    plc_id = g.plc_id
    var_id = [model.variable.id for model in g.variables]
    group_id = g.id

    # 设定变量组读取时间
    group_read_info = {
        'id': group_id,
        'plc_id': plc_id,
        'var_id': var_id,
        'read_time': start_time + acquisition_cycle,
        'read_cycle': acquisition_cycle
    }
    group_read_data = r.get('group_read')
    if isinstance(group_read_data, list):
        group_read_data.append(group_read_info)
    else:
        group_read_data = [group_read_info]
    r.set('group_read', group_read_data)


def redis_variable_info(r, g):
    # 设定变量信息
    variable_info = {
        'group_id': g.id,
        'variables': []
    }
    for var in g.variables:
        variable = var.variable
        var_info = {
            'id': variable.id,
            'db_num': variable.db_num,
            'address': variable.address,
            'data_type': variable.data_type,
            'area': variable.area,
            'is_analog': variable.is_analog,
            'analog_low_range': variable.analog_low_range,
            'analog_high_range': variable.analog_high_range,
            'digital_low_range': variable.digital_low_range,
            'digital_high_range': variable.digital_high_range,
            'offset': variable.offset
        }
        variable_info['variables'].append(var_info)

    variable_data = r.get('variable')
    if isinstance(variable_data, list):
        variable_data.append(variable_info)
    else:
        variable_data = [variable_info]
    r.set('variable', variable_data)
