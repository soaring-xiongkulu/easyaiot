from glob import iglob
from importlib import import_module
from flask_migrate import Migrate

from app.base.app import app
from app.base.ext import db


for view_path in iglob('**/view.py', recursive=True):
    view_path = view_path.replace('.py', '').replace('/', '.')
    import_module(view_path[view_path.find('module'):])

migrate = Migrate(app, db)