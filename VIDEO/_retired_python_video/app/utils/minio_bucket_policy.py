"""
MinIO 存储桶公开读写策略（供 Console /api/v1/buckets/.../objects/download 匿名访问）
"""
import json
import logging

from minio.error import S3Error

logger = logging.getLogger(__name__)


def build_public_read_write_policy(bucket_name: str) -> str:
    """构建 MinIO 桶公开读写策略 JSON 字符串。"""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:ListBucket",
                    "s3:ListBucketMultipartUploads",
                ],
                "Resource": [f"arn:aws:s3:::{bucket_name}"],
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": [
                    "s3:ListMultipartUploadParts",
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                ],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
            },
        ],
    }
    return json.dumps(policy)


def ensure_bucket_public_read_write_policy(minio_client, bucket_name: str) -> None:
    """确保桶存在公开读写策略；桶由业务代码创建时若未设策略会导致下载 500。"""
    try:
        if not minio_client.bucket_exists(bucket_name):
            return
        minio_client.set_bucket_policy(bucket_name, build_public_read_write_policy(bucket_name))
        logger.info("已确保 MinIO 桶公开策略: %s", bucket_name)
    except S3Error as e:
        logger.warning("设置 MinIO 桶公开策略失败 bucket=%s error=%s", bucket_name, e)
