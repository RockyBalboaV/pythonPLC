import psutil

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
    # 内存总量
    total_memory = int(psutil.virtual_memory()[0] / 1024 / 1024)
    # 空闲内存
    free_memory = int(psutil.virtual_memory()[4] / 1024 / 1024)
    # 发送流量
    bytes_sent = int(psutil.net_io_counters()[0] / 1024 / 1024)
    # 接收流量
    bytes_recv = int(psutil.net_io_counters()[1] / 1024 / 1024)

    info = {
        'boot_time': boot_time,
        'total_usage': total_usage,
        'free_usage': free_usage,
        'total_memory': total_memory,
        'free_memory': free_memory,
        'bytes_sent': bytes_sent,
        'bytes_recv': bytes_recv
    }

    return info


def redis_add_alarm_variables():
    session = Session()
    alarm_models = session.query(AlarmInfo).all()
    data = [
        {
            'variable_id': model.variable_id,
            'type': model.type,
            'bool': model.bool,
            'symbol': model.symbol,
            'limit': model.limit,
            'delay': model.delay
        }
        for model in alarm_models
    ]

    return data
