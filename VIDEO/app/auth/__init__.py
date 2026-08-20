"""VIDEO 本地认证（云边一体 · 单机合装 / edge 规格由 VIDEO 主导登录）。"""

from app.auth.auth_manager import AuthManager, get_auth_manager
from app.auth.token_service import create_token_pair, revoke_token, verify_access_token

__all__ = [
    "AuthManager",
    "get_auth_manager",
    "create_token_pair",
    "revoke_token",
    "verify_access_token",
]
