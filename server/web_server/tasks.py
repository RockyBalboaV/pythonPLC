import time
from web_server.models import db, YjStationInfo, TransferLog

from web_server.ext import celery
from web_server import current_app
from config import Config


@celery.task()
def test(msg):
    return msg


@celery.task()
def check_station():
    with current_app.app_context():
        current_time = int(time.time())
        stations = db.session.query(YjStationInfo)
        for s in stations:
            last_log = s.logs.order_by(TransferLog.time.desc()).first()
            if last_log:
                last_time = last_log.time
                last_level = last_log.level
                if current_time - last_time > Config.STATION_TIMEOUT:
                    warn_level = last_level + 1
                    if warn_level >= 3:
                        level = 3,
                        note = 'ERROR'
                    else:
                        level = warn_level,
                        note = 'WARNING'
                else:
                    level = 0,
                    note = 'OK'
            else:
                level = 0,
                note = 'First Check'

            warn = TransferLog(
                station_id=s.id,
                level=level,
                time=current_time,
                note=note
            )
            db.session.add(warn)
        db.session.commit()
