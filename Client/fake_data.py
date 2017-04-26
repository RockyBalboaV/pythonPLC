from models import *
import datetime, time

i = int()

value = Value('fake', 2, datetime.datetime.now(), 10)
session.add(value)
session.commit()


value = Value('fake', 1, datetime.datetime.now(), 1)
session.add(value)
session.commit()

