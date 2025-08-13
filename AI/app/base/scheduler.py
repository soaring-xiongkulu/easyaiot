import logging

import tzlocal
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone=tzlocal.get_localzone_name())
logging.getLogger('apscheduler').setLevel(logging.ERROR)
