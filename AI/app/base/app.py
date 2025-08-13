import mimetypes
import os

from flask import Flask, make_response, Blueprint, send_file
from flask_cors import CORS

from app.base.exception import AIManagerError
from app.config import FlaskConfig

app = Flask('easyaiot')
app.config.from_object(FlaskConfig)
CORS(app)

_blueprints = {}


def make_manager_response(data: dict = None, error: AIManagerError = None, ai_code: int = 200):
    resp = {'code': error.code, 'msg': error.msg} if error else {'code': 0, 'msg': None}
    if data:
        resp.update(data)
    return make_response(resp, ai_code)


def make_send_file_response(file_path: str, getting_error_cls: AIManagerError, not_exists_error_cls: AIManagerError):
    try:
        if not file_path:
            raise getting_error_cls(f'请传入文件的路径')
        if not os.path.exists(file_path):
            raise not_exists_error_cls(f'文件{file_path}不在服务器中')
        guess_mime = mimetypes.guess_type(file_path)
        if not guess_mime:
            raise getting_error_cls(f'无法将文件{file_path}根据拓展名转换为MimeType')
        return send_file(file_path, guess_mime[0])
    except AIManagerError as e:
        return make_manager_response(error=e, ai_code=404)


def make_send_file_response_web(file_path: str, getting_error_cls: AIManagerError,
                                not_exists_error_cls: AIManagerError):
    try:
        if not file_path:
            raise getting_error_cls(f'请传入文件的路径')
        if not os.path.exists(file_path):
            raise not_exists_error_cls(f'文件{file_path}不在服务器中')
        guess_mime = mimetypes.guess_type(file_path)
        if not guess_mime:
            raise getting_error_cls(f'无法将文件{file_path}根据拓展名转换为MimeType')
        return send_file(file_path, guess_mime[0], as_attachment=True)
    except AIManagerError as e:
        return make_manager_response(error=e, ai_code=404)

def get_blueprint(name, imort_name, **kwarge):
    bp = _blueprints.get(name)
    if not bp:
        bp = Blueprint(name, imort_name, url_prefix=f'/{name}', **kwarge)
        _blueprints[name] = bp
    return bp

def register_all_blueprints():
    for bp in _blueprints.values():
        app.register_blueprint(bp)
