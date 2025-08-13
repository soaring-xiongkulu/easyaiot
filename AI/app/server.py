import traceback
from glob import glob
from importlib import import_module

from app.config import config

from app.base.app import app, register_all_blueprints, make_manager_response
from app.base.exception import SystemInternalError, AIManagerError
from app.base.ext import db
from app.base.init import init_all
from app.base.logger import get_logger, init_logger
from app.base.scheduler import scheduler

logger = get_logger('server')

@app.errorhandler(Exception)
def handle_error(e):
    error_msg = f'系统内部错误[{str(e)}]：\n{traceback.format_exc()}'
    logger.error(error_msg)
    return make_manager_response(error=SystemInternalError(error_msg))

@app.errorhandler(AIManagerError)
def handle_error(e):
    return make_manager_response(error=e)

def import_views():
    views = glob('**/view.py', recursive=True)
    for view_path in views:
        view_path = view_path.replace('.py', '').replace('/', '.')
        import_module(view_path[view_path.find('module'):])

def server_init():
    init_logger()
    logger.info('程序启动...')
    # 注册所有视图
    register_all_blueprints()

    with app.app_context():
        db.create_all()
        init_all()
        scheduler.start()

import_views()

server_init()

if __name__ == '__main__':
    app.run('0.0.0.0', config._SERVER_PORT)
