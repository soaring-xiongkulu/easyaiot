"""
VIDEO 本地用户认证（SQLite + pbkdf2）。
空库时种子 admin / admin123。
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_auth_manager: Optional["AuthManager"] = None


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    """pbkdf2:sha256 字符串：pbkdf2:sha256:260000$salt$hash"""
    if salt is None:
        salt = secrets.token_hex(16)
    iterations = 260000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${dk.hex()}"


def _check_password(password_hash: str, password: str) -> bool:
    try:
        if password_hash.startswith("pbkdf2:sha256:"):
            rest = password_hash[len("pbkdf2:sha256:") :]
            iter_s, salt, hexhash = rest.split("$", 2)
            iterations = int(iter_s)
            dk = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
            )
            return secrets.compare_digest(dk.hex(), hexhash)
        from werkzeug.security import check_password_hash

        return check_password_hash(password_hash, password)
    except Exception:
        return False


class UserConfig:
    def __init__(
        self,
        id: int = None,
        username: str = "",
        password_hash: str = "",
        role: str = "user",
        display_name: str = "",
        email: str = "",
        enabled: int = 1,
        created_at: str = None,
        **kwargs,
    ):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.display_name = display_name
        self.email = email
        self.enabled = enabled
        self.created_at = created_at

    def to_dict(self, include_password: bool = False) -> Dict:
        data = {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name,
            "email": self.email,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }
        if include_password:
            data["password_hash"] = self.password_hash
        return data


class AuthManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    display_name VARCHAR(50) DEFAULT '',
                    email VARCHAR(100) DEFAULT '',
                    enabled INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                default_password = _hash_password("admin123")
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, display_name, enabled)
                    VALUES (?, ?, 'admin', '系统管理员', 1)
                    """,
                    ("admin", default_password),
                )
                logger.info("已创建默认管理员: admin / admin123")
            conn.commit()

    def _row_to_user(self, row) -> UserConfig:
        return UserConfig(
            id=row[0],
            username=row[1],
            password_hash=row[2],
            role=row[3],
            display_name=row[4] or "",
            email=row[5] if len(row) > 5 and row[5] else "",
            enabled=row[6] if len(row) > 6 else 1,
            created_at=row[7] if len(row) > 7 else None,
        )

    def authenticate(self, username: str, password: str) -> Optional[UserConfig]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, password_hash, role, display_name, email, enabled, created_at
                FROM users WHERE username = ?
                """,
                (username,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            user = self._row_to_user(row)
            if user.enabled != 1:
                return None
            if not _check_password(user.password_hash, password):
                return None
            return user

    def get_user(self, user_id: int) -> Optional[UserConfig]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, password_hash, role, display_name, email, enabled, created_at
                FROM users WHERE id = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[UserConfig]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, password_hash, role, display_name, email, enabled, created_at
                FROM users WHERE username = ?
                """,
                (username,),
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def get_all_users(self) -> List[UserConfig]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, password_hash, role, display_name, email, enabled, created_at
                FROM users ORDER BY created_at ASC
                """
            )
            return [self._row_to_user(row) for row in cursor.fetchall()]

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        user = self.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")
        if not _check_password(user.password_hash, old_password):
            raise ValueError("旧密码不正确")
        new_password = (new_password or "").strip()
        if len(new_password) < 4:
            raise ValueError("新密码长度不能少于 4 位")
        updated = self.update_user(user_id, {"password": new_password})
        if not updated:
            raise ValueError("修改密码失败")

    def create_user(self, data: Dict) -> UserConfig:
        username = (data.get("username") or "").strip()
        if not username:
            raise ValueError("用户名不能为空")
        if self.get_user_by_username(username):
            raise ValueError("用户名已存在")
        password = data.get("password") or ""
        if not password:
            raise ValueError("密码不能为空")
        password_hash = _hash_password(password)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, display_name, email, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    data.get("role", "user"),
                    data.get("display_name", ""),
                    data.get("email", ""),
                    int(data.get("enabled", 1)),
                    now,
                    now,
                ),
            )
            user_id = cursor.lastrowid
            conn.commit()
            return self.get_user(user_id)

    def update_user(self, user_id: int, data: Dict) -> Optional[UserConfig]:
        user = self.get_user(user_id)
        if not user:
            return None
        set_clauses = []
        params = []
        for field, col in (
            ("role", "role"),
            ("display_name", "display_name"),
            ("email", "email"),
            ("enabled", "enabled"),
        ):
            if field in data:
                set_clauses.append(f"{col} = ?")
                params.append(data[field])
        if data.get("password"):
            set_clauses.append("password_hash = ?")
            params.append(_hash_password(data["password"]))
        if not set_clauses:
            return user
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(user_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?",
                params,
            )
            conn.commit()
        return self.get_user(user_id)

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        if user.role == "admin":
            admins = [u for u in self.get_all_users() if u.role == "admin" and u.enabled == 1]
            if len(admins) <= 1:
                raise ValueError("不能删除最后一个管理员")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0


def default_auth_db_path() -> str:
    root = os.environ.get("VIDEO_AUTH_DB") or os.environ.get("EASYAIOT_VIDEO_AUTH_DB")
    if root:
        return root
    base = os.environ.get("EASYAIOT_MEDIA_ROOT") or "/data"
    candidate = os.path.join(base, "video-auth", "users.db")
    parent = os.path.dirname(candidate)
    if os.path.isdir(parent) and os.access(parent, os.W_OK):
        if not os.path.exists(candidate) or os.access(candidate, os.W_OK):
            return candidate
    fallback = os.path.join(os.path.expanduser("~"), ".easyaiot", "video-auth", "users.db")
    logger.warning(
        "媒体目录 auth 数据库不可写 (%s)，回退到本地路径: %s",
        candidate,
        fallback,
    )
    return fallback


def get_auth_manager() -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(default_auth_db_path())
    return _auth_manager


def reset_auth_manager() -> None:
    global _auth_manager
    _auth_manager = None
