"""S3/MinIO bucket naming helpers (Python-first certify fixtures).

AWS S3 bucket rules (subset): lowercase letters, digits, hyphens, dots;
no underscores. Certify fixtures derive bucket from space_code via hyphen slug.
"""

from __future__ import annotations

import re

_S3_BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


def certify_bucket_name(space_code: str) -> str:
    """Build S3-safe certify bucket from a space_code (may contain underscores)."""
    slug = space_code.strip().lower().replace("_", "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    return f"certify-{slug}"


def is_valid_s3_bucket_name(bucket_name: str) -> bool:
    if not bucket_name or "_" in bucket_name:
        return False
    return bool(_S3_BUCKET_RE.match(bucket_name.strip().lower()))


def bucket_name_error(bucket_name: str) -> str | None:
    if bucket_name is None or not str(bucket_name).strip():
        return "bucket_name 不能为空"
    name = str(bucket_name).strip()
    if "_" in name:
        return f"bucket_name 含非法字符 '_'（S3 不允许下划线）: {name}"
    if not is_valid_s3_bucket_name(name):
        return f"bucket_name 不符合 S3 命名规则: {name}"
    return None
