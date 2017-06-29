import time
import datetime
from flask import jsonify
from web_server.models import *

from web_server.ext import celery
from web_server import current_app


@celery.task()
def test(msg):
    return msg


@celery.task()
def check_station():
    with current_app.app_context():
        current_time = datetime.datetime.now()
        stations = db.session.query(YjStationInfo)
        for s in stations:
            s_last_log = s.logs.order_by(TransferLog.time.desc()).first()
            if s_last_log:
                last_time = datetime.datetime.fromtimestamp(s_last_log.time)
                last_level = s_last_log.level
                if (current_time - last_time).total_seconds() > 5:
                    warn_level = last_level + 1
                    if warn_level >= 3:
                        warn = TransferLog(station_id=s.id,
                                           level=3,
                                           time=int(time.mktime(current_time.timetuple())),
                                           note='ERROR')
                    else:
                        warn = TransferLog(station_id=s.id,
                                           level=last_level + 1,
                                           time=int(time.mktime(current_time.timetuple())),
                                           note='WARNING')
                else:
                    warn = TransferLog(station_id=s.id,
                                       level=0,
                                       time=int(time.mktime(current_time.timetuple())),
                                       note='OK')
            else:
                warn = TransferLog(station_id=s.id,
                                   level=0,
                                   time=int(time.mktime(current_time.timetuple())),
                                   note='First Check')
            db.session.add(warn)
        db.session.commit()
