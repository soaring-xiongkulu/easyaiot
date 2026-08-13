"""Gitee / GitHub OAuth + 本地会话（供 IDEA 门户使用）。"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger('easyaiot-idea.oauth')


def _env(name: str, default: str = '') -> str:
    return os.environ.get(name, default).strip()


@dataclass
class AuthUser:
    provider: str
    id: str
    login: str
    name: str
    avatar_url: str = ''
    email: str = ''

    @property
    def workspace_user(self) -> str:
        # 工作区目录名：provider-login，避免跨平台撞名
        raw = f'{self.provider}-{self.login}'
        cleaned = ''.join(ch if ch.isalnum() or ch in '._-' else '-' for ch in raw)
        return cleaned[:48] or f'{self.provider}-user'

    def public_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'id': self.id,
            'login': self.login,
            'name': self.name or self.login,
            'avatar_url': self.avatar_url,
            'email': self.email,
            'workspace_user': self.workspace_user,
        }


@dataclass
class ProviderConfig:
    id: str
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    user_url: str
    scope: str

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)


class SessionStore:
    def __init__(self, data_dir: str, ttl_seconds: int = 86400 * 7) -> None:
        self.path = os.path.join(data_dir, 'sessions.json')
        self.ttl = max(3600, ttl_seconds)
        os.makedirs(data_dir, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        if not os.path.isfile(self.path):
            return {}
        try:
            with open(self.path, encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        tmp = f'{self.path}.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        os.replace(tmp, self.path)

    def create(self, user: AuthUser) -> str:
        token = secrets.token_urlsafe(32)
        now = time.time()
        data = self._load()
        # 清理过期
        data = {
            k: v for k, v in data.items()
            if isinstance(v, dict) and float(v.get('exp', 0)) > now
        }
        data[token] = {
            'exp': now + self.ttl,
            'user': user.public_dict(),
        }
        self._save(data)
        return token

    def get(self, token: str) -> Optional[AuthUser]:
        if not token:
            return None
        data = self._load()
        item = data.get(token)
        if not isinstance(item, dict):
            return None
        if float(item.get('exp', 0)) < time.time():
            return None
        u = item.get('user') or {}
        return AuthUser(
            provider=str(u.get('provider') or ''),
            id=str(u.get('id') or ''),
            login=str(u.get('login') or ''),
            name=str(u.get('name') or ''),
            avatar_url=str(u.get('avatar_url') or ''),
            email=str(u.get('email') or ''),
        )

    def delete(self, token: str) -> None:
        data = self._load()
        if token in data:
            del data[token]
            self._save(data)


class OAuthService:
    def __init__(self, data_dir: str) -> None:
        self.redirect_base = _env('IDEA_OAUTH_REDIRECT_BASE')  # e.g. http://host:9300
        self.web_callback = _env('IDEA_WEB_CALLBACK') or (
            (self.redirect_base.rstrip('/') + '/') if self.redirect_base else '/'
        )
        self.state_secret = _env('IDEA_SESSION_SECRET') or secrets.token_hex(16)
        self.sessions = SessionStore(
            data_dir,
            ttl_seconds=int(_env('IDEA_SESSION_TTL_SECONDS', str(86400 * 7)) or str(86400 * 7)),
        )
        self.providers: Dict[str, ProviderConfig] = {
            'gitee': ProviderConfig(
                id='gitee',
                name='Gitee',
                client_id=_env('IDEA_GITEE_CLIENT_ID'),
                client_secret=_env('IDEA_GITEE_CLIENT_SECRET'),
                authorize_url='https://gitee.com/oauth/authorize',
                token_url='https://gitee.com/oauth/token',
                user_url='https://gitee.com/api/v5/user',
                scope=_env('IDEA_GITEE_SCOPE', 'user_info'),
            ),
            'github': ProviderConfig(
                id='github',
                name='GitHub',
                client_id=_env('IDEA_GITHUB_CLIENT_ID'),
                client_secret=_env('IDEA_GITHUB_CLIENT_SECRET'),
                authorize_url='https://github.com/login/oauth/authorize',
                token_url='https://github.com/login/oauth/access_token',
                user_url='https://api.github.com/user',
                scope=_env('IDEA_GITHUB_SCOPE', 'read:user user:email'),
            ),
        }
        self.required = _env('IDEA_OAUTH_REQUIRED', '0').lower() in ('1', 'true', 'yes')

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {'id': p.id, 'name': p.name, 'enabled': p.enabled}
            for p in self.providers.values()
        ]

    def enabled_ids(self) -> List[str]:
        return [p.id for p in self.providers.values() if p.enabled]

    def _callback_url(self, provider: str) -> str:
        base = self.redirect_base.rstrip('/')
        if not base:
            raise RuntimeError('IDEA_OAUTH_REDIRECT_BASE is required for OAuth')
        return f'{base}/api/auth/callback/{provider}'

    def _sign_state(self, provider: str) -> str:
        nonce = secrets.token_urlsafe(12)
        payload = f'{provider}:{int(time.time())}:{nonce}'
        sig = hmac.new(self.state_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
        return urllib.parse.quote(f'{payload}:{sig}', safe='')

    def _verify_state(self, provider: str, state: str) -> bool:
        try:
            raw = urllib.parse.unquote(state or '')
            parts = raw.split(':')
            if len(parts) != 4:
                return False
            prov, ts, _nonce, sig = parts
            if prov != provider:
                return False
            if abs(time.time() - int(ts)) > 600:
                return False
            payload = f'{prov}:{ts}:{_nonce}'
            expect = hmac.new(self.state_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
            return hmac.compare_digest(expect, sig)
        except (ValueError, TypeError):
            return False

    def authorize_url(self, provider: str) -> str:
        cfg = self.providers.get(provider)
        if not cfg or not cfg.enabled:
            raise RuntimeError(f'oauth provider not configured: {provider}')
        params = {
            'client_id': cfg.client_id,
            'redirect_uri': self._callback_url(provider),
            'response_type': 'code',
            'scope': cfg.scope,
            'state': self._sign_state(provider),
        }
        return f'{cfg.authorize_url}?{urllib.parse.urlencode(params)}'

    def _http_json(
        self,
        url: str,
        method: str = 'GET',
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        body = None
        hdrs = {'Accept': 'application/json', 'User-Agent': 'EasyAIoT-IDEA'}
        if headers:
            hdrs.update(headers)
        if data is not None:
            body = urllib.parse.urlencode(data).encode()
            hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'oauth http {exc.code}: {detail[:300]}') from exc
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # GitHub 偶发返回 querystring
            parsed = urllib.parse.parse_qs(raw)
            return {k: v[0] if isinstance(v, list) and v else v for k, v in parsed.items()}

    def exchange_code(self, provider: str, code: str) -> AuthUser:
        cfg = self.providers.get(provider)
        if not cfg or not cfg.enabled:
            raise RuntimeError(f'oauth provider not configured: {provider}')
        token_payload = {
            'client_id': cfg.client_id,
            'client_secret': cfg.client_secret,
            'code': code,
            'redirect_uri': self._callback_url(provider),
            'grant_type': 'authorization_code',
        }
        token_resp = self._http_json(cfg.token_url, method='POST', data=token_payload)
        access_token = token_resp.get('access_token')
        if not access_token:
            raise RuntimeError(f'oauth token missing: {token_resp}')

        if provider == 'gitee':
            user_resp = self._http_json(
                f'{cfg.user_url}?{urllib.parse.urlencode({"access_token": access_token})}'
            )
        else:
            user_resp = self._http_json(
                cfg.user_url,
                headers={'Authorization': f'Bearer {access_token}'},
            )

        login = str(user_resp.get('login') or user_resp.get('username') or '')
        if not login:
            raise RuntimeError(f'oauth user login missing: {user_resp}')
        return AuthUser(
            provider=provider,
            id=str(user_resp.get('id') or login),
            login=login,
            name=str(user_resp.get('name') or login),
            avatar_url=str(user_resp.get('avatar_url') or ''),
            email=str(user_resp.get('email') or ''),
        )

    def finish_login(self, provider: str, code: str, state: str) -> tuple[str, AuthUser]:
        if not self._verify_state(provider, state):
            raise RuntimeError('invalid oauth state')
        user = self.exchange_code(provider, code)
        token = self.sessions.create(user)
        return token, user

    def web_redirect(self, session_token: str, error: str = '') -> str:
        target = self.web_callback or '/'
        parts = urllib.parse.urlparse(target)
        q = dict(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
        if error:
            q['idea_error'] = error
            q.pop('idea_token', None)
        else:
            q['idea_token'] = session_token
            q.pop('idea_error', None)
        new_query = urllib.parse.urlencode(q)
        return urllib.parse.urlunparse(parts._replace(query=new_query))

    def user_from_request_token(self, token: str) -> Optional[AuthUser]:
        return self.sessions.get(token)
