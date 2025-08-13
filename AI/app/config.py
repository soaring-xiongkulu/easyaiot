import base64
import json
import logging
import os
from datetime import timedelta
from threading import Lock

_config_file_lock = Lock()

class FlaskConfig:
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:lf123456789@14.18.122.2:3306/easyaiot?charset=utf8'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SECRET_KEY = str(base64.b64encode(os.urandom(32)), 'utf8')

class Config:
    _CONFIG_PATH = '/usr/local/easyaiot/config.json'
    _LOGGER_LEVEL = logging.DEBUG
    _SERVER_PORT = 5000

    def load_config(self):
        with open(self._CONFIG_PATH, 'r') as cf:
            config = json.load(cf)
        for k, v in config.items():
            setattr(self, k, v)

    def save_config(self):
        with _config_file_lock:
            with open(self._CONFIG_PATH, 'w') as cf:
                json.dump({
                    k: getattr(self, k) \
                    for k in filter(lambda k: not k.startswith('_') and k.isupper(), dir(config))
                }, cf)

config = Config()
