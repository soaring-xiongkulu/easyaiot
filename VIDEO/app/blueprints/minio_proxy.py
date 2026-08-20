"""
MinIO 对象下载代理（兼容 Console API 路径格式）

数据库与业务层常保存相对路径：
  /api/v1/buckets/{bucket}/objects/download?prefix={object_key}

算法服务等会将该路径拼到 AI_SERVICE_URL 上拉取模型；AI 模块需代理到 MinIO S3 API。
"""
import logging
import mimetypes
import os
from urllib.parse import quote, unquote

from flask import Blueprint, Response, request
from minio.error import S3Error
from werkzeug.utils import secure_filename

from app.services.minio_service import ModelService, parse_minio_download_url

minio_proxy_bp = Blueprint('minio_proxy', __name__)
logger = logging.getLogger(__name__)


def _build_content_disposition(disposition: str, filename: str) -> str:
    fallback = secure_filename(filename)
    extension = os.path.splitext(filename)[1]
    if not (
        extension.startswith('.')
        and len(extension) <= 16
        and extension[1:].isascii()
        and extension[1:].isalnum()
    ):
        extension = ''
    if not fallback or fallback == extension.lstrip('.'):
        fallback = f'download{extension}'

    if filename.isascii() and fallback == filename:
        return f'{disposition}; filename="{fallback}"'
    encoded_filename = quote(filename, safe='')
    return (
        f'{disposition}; filename="{fallback}"; '
        f"filename*=UTF-8''{encoded_filename}"
    )


@minio_proxy_bp.route('/api/v1/buckets/<bucket_name>/objects/download', methods=['GET'])
def download_object(bucket_name: str):
    """代理 MinIO 对象下载，兼容 MinIO Console 的 download API 路径。"""
    prefix = request.args.get('prefix')
    if not prefix:
        return Response('缺少 prefix 参数', status=400, mimetype='text/plain')

    object_key = unquote(prefix)
    _, object_key_from_url = parse_minio_download_url(
        f'/api/v1/buckets/{bucket_name}/objects/download?prefix={prefix}'
    )
    if object_key_from_url:
        object_key = object_key_from_url

    from app.utils.service_urls import minio_storage_enabled
    from app.services.local_storage_service import read_local_object

    if not minio_storage_enabled():
        content, content_type, err = read_local_object(bucket_name, object_key)
        if err or content is None:
            logger.warning('本地对象不存在: %s/%s', bucket_name, object_key)
            return Response(err or '对象不存在', status=404, mimetype='text/plain')
        filename = os.path.basename(object_key) or 'download'
        response = Response(content, mimetype=content_type or 'application/octet-stream')
        response.headers['Content-Disposition'] = _build_content_disposition('inline', filename)
        response.headers['Content-Length'] = str(len(content))
        return response

    try:
        client = ModelService.get_minio_client()
        if not client.bucket_exists(bucket_name):
            return Response(f'MinIO 存储桶不存在: {bucket_name}', status=404, mimetype='text/plain')

        stat = client.stat_object(bucket_name, object_key)
        data = client.get_object(bucket_name, object_key)
        content = data.read()
        data.close()
        data.release_conn()

        filename = os.path.basename(object_key) or 'download'
        content_type = stat.content_type
        if not content_type or content_type == 'application/octet-stream':
            guessed, _ = mimetypes.guess_type(filename)
            content_type = guessed or 'application/octet-stream'

        response = Response(content, mimetype=content_type)
        response.headers['Content-Disposition'] = _build_content_disposition('attachment', filename)
        response.headers['Content-Length'] = str(len(content))
        return response
    except S3Error as e:
        if getattr(e, 'code', '') == 'NoSuchKey':
            logger.warning('MinIO 对象不存在: %s/%s', bucket_name, object_key)
            return Response(f'对象不存在: {bucket_name}/{object_key}', status=404, mimetype='text/plain')
        logger.error('MinIO 下载失败: %s/%s, %s', bucket_name, object_key, e)
        return Response(f'MinIO 下载失败: {e}', status=500, mimetype='text/plain')
    except Exception as e:
        logger.error('代理下载异常: %s/%s, %s', bucket_name, object_key, e, exc_info=True)
        return Response(f'下载失败: {e}', status=500, mimetype='text/plain')
