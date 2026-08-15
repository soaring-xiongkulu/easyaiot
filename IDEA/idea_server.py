"""IDEA HTTP API：工作区编排 + OAuth + 健康检查。"""
from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Callable, Optional

from flask import Flask, jsonify, redirect, request, send_from_directory

from idle_reaper import IdleReaper
from oauth_auth import OAuthService
from publish_ops import PublishOps
from workspace_ops import WorkspaceOps

logger = logging.getLogger('easyaiot-idea.server')

IDEA_TOKEN = os.environ.get('IDEA_TOKEN', '').strip()
IDEA_LISTEN_HOST = os.environ.get('IDEA_LISTEN_HOST', '0.0.0.0')
IDEA_LISTEN_PORT = int(os.environ.get('IDEA_LISTEN_PORT', '9300'))
IDEA_IDLE_TIMEOUT_HOURS = float(os.environ.get('IDEA_IDLE_TIMEOUT_HOURS', '8') or '8')
IDEA_IDLE_CHECK_SECONDS = int(os.environ.get('IDEA_IDLE_CHECK_SECONDS', '600') or '600')


def _request_host() -> Optional[str]:
    xf = (request.headers.get('X-Forwarded-Host') or '').split(',')[0].strip()
    if xf:
        return xf
    return request.host


def _json_error(message: str, status: int = 400):
    return jsonify({'ok': False, 'error': message}), status


def _bearer_token(header_val: str) -> str:
    value = (header_val or '').strip()
    if value.lower().startswith('bearer '):
        return value[7:].strip()
    return value


WEBUI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webui')


def create_app() -> Flask:
    app = Flask('easyaiot-idea')
    ops = WorkspaceOps()
    oauth = OAuthService(ops.data_dir)
    publisher = PublishOps(ops)
    reaper = IdleReaper(ops, IDEA_IDLE_TIMEOUT_HOURS, IDEA_IDLE_CHECK_SECONDS)
    reaper.start()
    app.extensions['idea_ops'] = ops
    app.extensions['idea_oauth'] = oauth
    app.extensions['idea_reaper'] = reaper
    app.extensions['idea_publish'] = publisher

    def _session_token_from_request() -> str:
        return (
            request.headers.get('X-IDEA-Session')
            or request.args.get('idea_token')
            or ''
        ).strip()

    def _current_user():
        return oauth.user_from_request_token(_session_token_from_request())

    def _actor_user() -> str:
        user = _current_user()
        if user:
            return user.workspace_user
        body = request.get_json(silent=True) or {}
        return (
            (request.args.get('user') or body.get('user') or 'contributor')
        ).strip() or 'contributor'

    def require_access(fn: Callable):
        """允许：服务令牌 / 用户会话；OAuth 强制或配置了 IDEA_TOKEN 时不可匿名。"""
        @wraps(fn)
        def wrapper(*args, **kwargs):
            service_ok = False
            if IDEA_TOKEN:
                got = request.headers.get('X-IDEA-Token') or _bearer_token(
                    request.headers.get('Authorization', '')
                )
                service_ok = got == IDEA_TOKEN
            user = _current_user()
            if service_ok or user:
                return fn(*args, **kwargs)
            if oauth.required or IDEA_TOKEN:
                return _json_error('login required', 401)
            return fn(*args, **kwargs)
        return wrapper

    @app.after_request
    def cors(resp):
        origin = request.headers.get('Origin', '*') or '*'
        resp.headers['Access-Control-Allow-Origin'] = origin
        resp.headers['Access-Control-Allow-Headers'] = (
            'Content-Type, X-IDEA-Token, X-IDEA-Session, Authorization'
        )
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        return resp

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'ok': True, 'service': 'easyaiot-idea'})

    # ---------- Auth ----------
    @app.route('/api/auth/providers', methods=['GET', 'OPTIONS'])
    def auth_providers():
        if request.method == 'OPTIONS':
            return '', 204
        return jsonify({
            'ok': True,
            'data': {
                'providers': oauth.list_providers(),
                'required': oauth.required,
                'redirect_base': oauth.redirect_base,
            },
        })

    @app.route('/api/auth/login/<provider>', methods=['GET'])
    def auth_login(provider: str):
        try:
            return redirect(oauth.authorize_url(provider))
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 400)

    @app.route('/api/auth/callback/<provider>', methods=['GET'])
    def auth_callback(provider: str):
        err = request.args.get('error')
        if err:
            return redirect(oauth.web_redirect('', error=str(err)))
        code = request.args.get('code') or ''
        state = request.args.get('state') or ''
        try:
            token, _user = oauth.finish_login(provider, code, state)
            return redirect(oauth.web_redirect(token))
        except Exception as exc:  # noqa: BLE001
            logger.exception('oauth callback failed')
            return redirect(oauth.web_redirect('', error=str(exc)[:180]))

    @app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
    def auth_me():
        if request.method == 'OPTIONS':
            return '', 204
        user = _current_user()
        if not user:
            return jsonify({'ok': True, 'data': None})
        return jsonify({'ok': True, 'data': user.public_dict()})

    @app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
    def auth_logout():
        if request.method == 'OPTIONS':
            return '', 204
        token = _session_token_from_request()
        if token:
            oauth.sessions.delete(token)
        return jsonify({'ok': True, 'data': {'logged_out': True}})

    # ---------- Workspaces ----------
    @app.route('/api/stats', methods=['GET', 'OPTIONS'])
    @require_access
    def stats():
        if request.method == 'OPTIONS':
            return '', 204
        return jsonify({'ok': True, 'data': ops.stats()})

    @app.route('/api/workspaces', methods=['GET', 'POST', 'OPTIONS'])
    @require_access
    def workspaces():
        if request.method == 'OPTIONS':
            return '', 204
        host = _request_host()
        user = _current_user()

        if request.method == 'GET':
            scope = (request.args.get('scope') or '').strip().lower()
            query_user = (request.args.get('user') or '').strip() or None
            service_ok = False
            if IDEA_TOKEN:
                got = request.headers.get('X-IDEA-Token') or _bearer_token(
                    request.headers.get('Authorization', '')
                )
                service_ok = got == IDEA_TOKEN
            viewer_user = user.workspace_user if user else None
            # 本机未强制 OAuth 时，门户本身就是管理面，列表需带回登录密码
            include_password = bool(service_ok or (user is None and not oauth.required))
            if scope == 'all':
                data = ops.list_workspaces(
                    user=None,
                    request_host=host,
                    viewer_user=viewer_user,
                    include_password=include_password,
                )
            else:
                if user and not service_ok:
                    query_user = user.workspace_user
                data = ops.list_workspaces(
                    user=query_user,
                    request_host=host,
                    viewer_user=viewer_user,
                    include_password=include_password,
                )
            return jsonify({'ok': True, 'data': data})

        body = request.get_json(silent=True) or {}
        profile: dict = {}
        if user:
            ws_user = user.workspace_user
            profile = {
                'provider': user.provider,
                'login': user.login,
                'name': user.name,
                'email': user.email,
                'fork_url': (body.get('fork_url') or '').strip(),
            }
        else:
            ws_user = (body.get('user') or request.args.get('user') or 'contributor').strip()
            profile = {
                'provider': (body.get('provider') or '').strip(),
                'login': (body.get('login') or '').strip(),
                'name': (body.get('name') or '').strip(),
                'email': (body.get('email') or '').strip(),
                'fork_url': (body.get('fork_url') or '').strip(),
            }
        password = (body.get('password') or '').strip() or None
        try:
            data = ops.create_workspace(
                user=ws_user,
                request_host=host,
                password=password,
                profile=profile,
            )
            return jsonify({'ok': True, 'data': data})
        except Exception as exc:  # noqa: BLE001
            logger.exception('create workspace failed')
            return _json_error(str(exc), 500)

    @app.route('/api/workspaces/<workspace_id>', methods=['GET', 'DELETE', 'OPTIONS'])
    @require_access
    def workspace_detail(workspace_id: str):
        if request.method == 'OPTIONS':
            return '', 204
        host = _request_host()
        if request.method == 'GET':
            data = ops.get_workspace(workspace_id, request_host=host)
            if not data:
                return _json_error('workspace not found', 404)
            user = _current_user()
            if user and data.get('user') != user.workspace_user:
                # 允许服务令牌
                if IDEA_TOKEN:
                    got = request.headers.get('X-IDEA-Token') or _bearer_token(
                        request.headers.get('Authorization', '')
                    )
                    if got != IDEA_TOKEN:
                        return _json_error('forbidden', 403)
                else:
                    return _json_error('forbidden', 403)
            ops.touch_activity(workspace_id)
            return jsonify({'ok': True, 'data': ops.get_workspace(workspace_id, request_host=host)})
        try:
            data = ops.get_workspace(workspace_id, request_host=host)
            user = _current_user()
            if user and data and data.get('user') != user.workspace_user:
                if IDEA_TOKEN:
                    got = request.headers.get('X-IDEA-Token') or _bearer_token(
                        request.headers.get('Authorization', '')
                    )
                    if got != IDEA_TOKEN:
                        return _json_error('forbidden', 403)
                else:
                    return _json_error('forbidden', 403)
            remove_data = (request.args.get('remove_data') or '').lower() in ('1', 'true', 'yes')
            result = ops.delete_workspace(workspace_id, remove_data=remove_data)
            return jsonify({'ok': True, 'data': result})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 404)

    def _assert_workspace_access(workspace_id: str):
        data = ops.get_workspace(workspace_id)
        if not data:
            return None, _json_error('workspace not found', 404)
        user = _current_user()
        if user and data.get('user') != user.workspace_user:
            if IDEA_TOKEN:
                got = request.headers.get('X-IDEA-Token') or _bearer_token(
                    request.headers.get('Authorization', '')
                )
                if got != IDEA_TOKEN:
                    return None, _json_error('forbidden', 403)
            else:
                return None, _json_error('forbidden', 403)
        return data, None

    @app.route('/api/workspaces/<workspace_id>/stop', methods=['POST', 'OPTIONS'])
    @require_access
    def workspace_stop(workspace_id: str):
        if request.method == 'OPTIONS':
            return '', 204
        _, err = _assert_workspace_access(workspace_id)
        if err:
            return err
        try:
            data = ops.stop_workspace(workspace_id, request_host=_request_host())
            return jsonify({'ok': True, 'data': data})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 404)

    @app.route('/api/workspaces/<workspace_id>/start', methods=['POST', 'OPTIONS'])
    @require_access
    def workspace_start(workspace_id: str):
        if request.method == 'OPTIONS':
            return '', 204
        _, err = _assert_workspace_access(workspace_id)
        if err:
            return err
        try:
            data = ops.start_workspace(workspace_id, request_host=_request_host())
            return jsonify({'ok': True, 'data': data})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 404)

    @app.route('/api/workspaces/<workspace_id>/heartbeat', methods=['POST', 'OPTIONS'])
    @require_access
    def workspace_heartbeat(workspace_id: str):
        if request.method == 'OPTIONS':
            return '', 204
        try:
            data = ops.heartbeat(workspace_id, request_host=_request_host())
            return jsonify({'ok': True, 'data': data})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 404)

    @app.route('/api/workspaces/<workspace_id>/open-file', methods=['POST', 'OPTIONS'])
    @require_access
    def workspace_open_file(workspace_id: str):
        """在 code-server 中打开仓库文件（IPC），供 HARNESS 点击引用时调用。"""
        if request.method == 'OPTIONS':
            return '', 204
        _, err = _assert_workspace_access(workspace_id)
        if err:
            return err
        body = request.get_json(silent=True) or {}
        path = (body.get('path') or body.get('file') or '').strip()
        if not path:
            return _json_error('path required', 400)
        try:
            data = ops.open_file(workspace_id, path)
            return jsonify({'ok': True, 'data': data})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 400)

    @app.route('/api/reap-idle', methods=['POST', 'OPTIONS'])
    @require_access
    def reap_idle():
        if request.method == 'OPTIONS':
            return '', 204
        # 仅服务令牌可触发全局回收
        if IDEA_TOKEN:
            got = request.headers.get('X-IDEA-Token') or _bearer_token(
                request.headers.get('Authorization', '')
            )
            if got != IDEA_TOKEN:
                return _json_error('forbidden', 403)
        return jsonify({'ok': True, 'data': ops.reap_idle_workspaces()})

    # ---------- Publish (本机替换) ----------
    @app.route('/api/publish/meta', methods=['GET', 'OPTIONS'])
    @require_access
    def publish_meta():
        if request.method == 'OPTIONS':
            return '', 204
        return jsonify({
            'ok': True,
            'data': {
                'allow': publisher.allow,
                'host_root': publisher.host_root,
                'live_url': publisher.live_url_for(_request_host()),
            },
        })

    @app.route('/api/publish/modules', methods=['GET', 'OPTIONS'])
    @require_access
    def publish_modules():
        if request.method == 'OPTIONS':
            return '', 204
        return jsonify({'ok': True, 'data': publisher.list_modules()})

    @app.route('/api/publish/suggest', methods=['GET', 'OPTIONS'])
    @require_access
    def publish_suggest():
        if request.method == 'OPTIONS':
            return '', 204
        try:
            return jsonify({'ok': True, 'data': publisher.suggest(_actor_user())})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 400)

    @app.route('/api/publish', methods=['POST', 'OPTIONS'])
    @require_access
    def publish_start():
        if request.method == 'OPTIONS':
            return '', 204
        body = request.get_json(silent=True) or {}
        modules = body.get('modules') or []
        if not modules and body.get('module'):
            modules = [body.get('module')]
        action = (body.get('action') or 'publish').strip()
        try:
            job = publisher.start_job(_actor_user(), list(modules), action=action)
            return jsonify({'ok': True, 'data': job})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 400)

    @app.route('/api/publish/jobs/<job_id>', methods=['GET', 'OPTIONS'])
    @require_access
    def publish_job(job_id: str):
        if request.method == 'OPTIONS':
            return '', 204
        job = publisher.get_job(job_id)
        if not job:
            cur = publisher.current_job()
            if cur and cur.get('id') == job_id:
                job = cur
        if not job:
            return _json_error('job not found', 404)
        return jsonify({'ok': True, 'data': job})

    @app.route('/api/git/remotes', methods=['GET', 'PUT', 'OPTIONS'])
    @require_access
    def git_remotes():
        if request.method == 'OPTIONS':
            return '', 204
        actor = _actor_user()
        if request.method == 'GET':
            return jsonify({'ok': True, 'data': publisher.git_remotes(actor)})
        body = request.get_json(silent=True) or {}
        try:
            data = publisher.set_origin(actor, (body.get('origin') or '').strip())
            return jsonify({'ok': True, 'data': data})
        except Exception as exc:  # noqa: BLE001
            return _json_error(str(exc), 400)

    @app.route('/static/<path:name>', methods=['GET'])
    def webui_static(name: str):
        return send_from_directory(WEBUI_DIR, name)

    @app.route('/', methods=['GET'])
    def index():
        want_json = 'application/json' in (request.headers.get('Accept') or '')
        if want_json and 'text/html' not in (request.headers.get('Accept') or ''):
            return jsonify({
                'service': 'EasyAIoT IDEA',
                'ui': '/',
                'health': '/health',
                'auth': '/api/auth/providers',
                'workspaces': '/api/workspaces',
                'publish': '/api/publish',
                'idle_timeout_hours': IDEA_IDLE_TIMEOUT_HOURS,
                'oauth_required': oauth.required,
            })
        resp = send_from_directory(WEBUI_DIR, 'index.html')
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    return app


def run_server(app: Flask) -> None:
    logger.info('IDEA portal listening on %s:%s', IDEA_LISTEN_HOST, IDEA_LISTEN_PORT)
    app.run(host=IDEA_LISTEN_HOST, port=IDEA_LISTEN_PORT, threaded=True)
