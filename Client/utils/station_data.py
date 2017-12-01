import psutil
import time

from utils.redis_middle_class import ConnDB
from models import serialize, Session, StationAlarm, PLCAlarm, AlarmInfo


def beats_data(id_num, session, con_time, current_time):
    r = ConnDB()
    # 获取心跳间隔时间内产生的报警
    alarm_data = r.get('alarm_info')

    # 获取
    station_alarms = list()
    plc_alarms = list()
    if con_time:
        station = session.query(StationAlarm).filter(con_time <= StationAlarm.time). \
            filter(StationAlarm.time < current_time).all()
        for s in station:
            station_alarms.append(serialize(s))

        plc = session.query(PLCAlarm).filter(PLCAlarm.level >= 2). \
            filter(con_time <= PLCAlarm.time).filter(PLCAlarm.time < current_time).all()
        for p in plc:
            plc_alarms.append(serialize(p))

    # 获取设备信息
    info = station_info()

    data = {
        'id_num': id_num,
        'station_alarms': station_alarms,
        'plc_alarms': plc_alarms,
        'station_info': info,
        'data_alarms': alarm_data
    }

    return data


def station_info():
    # 开机时间
    boot_time = int(psutil.boot_time())
    # 硬盘总量
    total_usage = int(psutil.disk_usage('/')[0] / 1024 / 1024)
    # 空闲容量
    free_usage = int(psutil.disk_usage('/')[2] / 1024 / 1024)
    # 使用容量百分比
    usage_percent = psutil.disk_usage('/')[3]

    # 内存总量
    total_memory = int(psutil.virtual_memory()[0] / 1024 / 1024)
    # 空闲内存
    free_memory = int(psutil.virtual_memory()[4] / 1024 / 1024)
    # 使用内存百分比
    memory_percent = psutil.virtual_memory()[2]

    # 发送流量
    bytes_sent = int(psutil.net_io_counters()[0] / 1024 / 1024)
    # 接收流量
    bytes_recv = int(psutil.net_io_counters()[1] / 1024 / 1024)
    # cpu占用
    cpu_percent = psutil.cpu_percent()

    info = {
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
    session = Session()
    alarm_models = session.query(AlarmInfo).all()
    if alarm_models:
        data = [
            {
                'variable_id': model.variable_id,
                'type': model.type,
                'symbol': model.symbol,
                'limit': model.limit,
                'delay': model.delay
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
    variable_id = [model.variable.id for model in g.variables]
    group_id = g.id
    server_record_cycle = g.server_record_cycle
    group_name = g.group_name

    # 设定变量组初始上传时间,
    group_upload_info = {
        'id': group_id,
        'plc_id': plc_id,
        'upload_time': start_time + upload_cycle,
        'is_uploading': False,
        'upload_cycle': upload_cycle,
        'server_record_cycle': server_record_cycle,
        'variable_id': variable_id,
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
    variable_id = [model.variable.id for model in g.variables]
    group_id = g.id

    # 设定变量组读取时间
    group_read_info = {
        'id': group_id,
        'plc_id': plc_id,
        'variable_id': variable_id,
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