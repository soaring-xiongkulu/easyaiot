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

from flask import Blueprint, Response, request, send_file, stream_with_context
from minio.error import S3Error
from werkzeug.utils import secure_filename

from app.services.minio_service import ModelService, parse_minio_download_url

minio_proxy_bp = Blueprint('minio_proxy', __name__)
logger = logging.getLogger(__name__)
_STREAM_CHUNK_SIZE = 1024 * 1024


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


def _parse_single_range(range_header: str, object_size: int):
    """解析单段 bytes Range；无 Range 返回 None，非法或越界抛出 ValueError。"""
    if not range_header:
        return None
    if not range_header.startswith('bytes=') or ',' in range_header:
        raise ValueError('仅支持单段 bytes Range')
    spec = range_header[6:].strip()
    if '-' not in spec or object_size < 0:
        raise ValueError('Range 格式错误')
    start_raw, end_raw = spec.split('-', 1)
    try:
        if start_raw:
            start = int(start_raw)
            end = int(end_raw) if end_raw else object_size - 1
            if start < 0 or start >= object_size or end < start:
                raise ValueError('Range 越界')
            end = min(end, object_size - 1)
        else:
            suffix_length = int(end_raw)
            if suffix_length <= 0 or object_size <= 0:
                raise ValueError('Range 越界')
            start = max(0, object_size - suffix_length)
            end = object_size - 1
    except (TypeError, ValueError) as exc:
        raise ValueError('Range 格式错误或越界') from exc
    return start, end


def _iter_minio_response(data, length: int):
    remaining = max(0, int(length))
    try:
        while remaining > 0:
            chunk = data.read(min(_STREAM_CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
    finally:
        data.close()
        data.release_conn()


@minio_proxy_bp.route('/api/v1/buckets/<bucket_name>/objects/download', methods=['GET', 'HEAD'])
def download_object(bucket_name: str):
    """流式代理对象下载，支持视频播放所需的 HEAD/Range。"""
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
    from app.services.local_storage_service import ensure_local_object

    if not minio_storage_enabled():
        try:
            local_path = ensure_local_object(bucket_name, object_key)
        except ValueError:
            return Response('对象路径非法', status=400, mimetype='text/plain')
        if not local_path:
            logger.warning('本地对象不存在: %s/%s', bucket_name, object_key)
            return Response('对象不存在', status=404, mimetype='text/plain')
        filename = os.path.basename(object_key) or 'download'
        response = send_file(
            local_path,
            conditional=True,
            as_attachment=False,
            download_name=filename,
        )
        response.headers['Content-Disposition'] = _build_content_disposition('inline', filename)
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    try:
        client = ModelService.get_minio_client()
        if not client.bucket_exists(bucket_name):
            return Response(f'MinIO 存储桶不存在: {bucket_name}', status=404, mimetype='text/plain')

        stat = client.stat_object(bucket_name, object_key)
        filename = os.path.basename(object_key) or 'download'
        content_type = stat.content_type
        if not content_type or content_type == 'application/octet-stream':
            guessed, _ = mimetypes.guess_type(filename)
            content_type = guessed or 'application/octet-stream'

        object_size = int(getattr(stat, 'size', 0) or 0)
        try:
            byte_range = _parse_single_range(request.headers.get('Range', ''), object_size)
        except ValueError:
            response = Response(status=416)
            response.headers['Content-Range'] = f'bytes */{object_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            return response

        start, end = byte_range if byte_range is not None else (0, object_size - 1)
        length = object_size if byte_range is None else end - start + 1
        status = 206 if byte_range is not None else 200
        if request.method == 'HEAD':
            response = Response(status=status, mimetype=content_type)
        else:
            data = client.get_object(
                bucket_name,
                object_key,
                offset=start,
                length=length,
            )
            response = Response(
                stream_with_context(_iter_minio_response(data, length)),
                status=status,
                mimetype=content_type,
                direct_passthrough=True,
            )
        disposition = 'inline' if content_type.startswith(('image/', 'video/')) else 'attachment'
        response.headers['Content-Disposition'] = _build_content_disposition(disposition, filename)
        response.headers['Content-Length'] = str(length)
        response.headers['Accept-Ranges'] = 'bytes'
        if byte_range is not None:
            response.headers['Content-Range'] = f'bytes {start}-{end}/{object_size}'
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
