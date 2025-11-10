"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os

from flask import Blueprint, request, jsonify, current_app
from flask import after_this_request
from werkzeug.utils import secure_filename

from app.services.ocr_service import OCRService
from models import OCRResult

# 配置日志
logger = logging.getLogger(__name__)

ocr_bp = Blueprint('ocr', __name__, url_prefix='/api/ocr')

# 初始化OCR服务
ocr_service = OCRService()

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'pdf'}
# 文件上传大小限制 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_request():
    """验证请求和文件"""
    if 'file' not in request.files:
        return False, "没有文件部分"

    file = request.files['file']
    if file.filename == '':
        return False, "未选择文件"

    if not allowed_file(file.filename):
        return False, "不支持的文件类型"

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)  # 重置文件指针

    if file_length > MAX_FILE_SIZE:
        return False, "文件过大，请上传小于10MB的文件"

    return True, file


@ocr_bp.route('/health', methods=['GET'])
def health_check():
    """
    服务健康检查端点
    ---
    tags:
      - OCR服务
    responses:
      200:
        description: 服务状态正常
      500:
        description: 服务异常
    """
    try:
        success, message = ocr_service.verify_service_connectivity()
        status_code = 200 if success else 500
        return jsonify({
            "status": "healthy" if success else "unhealthy",
            "message": message,
            "service_info": ocr_service.get_performance_metrics()
        }), status_code
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": f"服务异常: {str(e)}"
        }), 500


@ocr_bp.route('/process', methods=['POST'])
def process_image():
    """
    OCR处理端点 - 上传图像并进行OCR识别
    ---
    tags:
      - OCR服务
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: 要处理的图像文件
      - in: formData
        name: save_to_db
        type: boolean
        required: false
        default: true
        description: 是否将结果保存到数据库
      - in: formData
        name: preprocess
        type: boolean
        required: false
        default: false
        description: 是否进行图像预处理
      - in: formData
        name: upload_to_oss
        type: boolean
        required: false
        default: true
        description: 是否上传图片到OSS
    responses:
      200:
        description: OCR处理成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    # 验证请求和文件
    is_valid, result = validate_file_request()
    if not is_valid:
        return jsonify({"error": result}), 400

    file = result
    save_to_db = request.form.get('save_to_db', 'true').lower() == 'true'
    preprocess = request.form.get('preprocess', 'false').lower() == 'true'
    upload_to_oss = request.form.get('upload_to_oss', 'true').lower() == 'true'  # 新增

    try:
        # 创建临时文件路径
        filename = secure_filename(file.filename)
        temp_dir = current_app.config.get('UPLOAD_FOLDER', '/tmp')
        os.makedirs(temp_dir, exist_ok=True)

        input_path = os.path.join(temp_dir, f"input_{filename}")
        file.save(input_path)

        # 图像预处理（可选）
        image_path = input_path
        if preprocess:
            output_path = os.path.join(temp_dir, f"preprocessed_{filename}")
            image_path = ocr_service.preprocess_image(input_path, output_path)

        # 执行OCR处理（新增upload_to_oss参数）
        ocr_results = ocr_service.process_image(
            image_path,
            save_to_db=save_to_db,
            upload_to_oss=upload_to_oss  # 新增
        )

        # 清理临时文件
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if preprocess and os.path.exists(image_path) and image_path != input_path:
                    os.remove(image_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            return response

        # 返回处理结果
        if "error" in ocr_results:
            return jsonify(ocr_results), 500

        return jsonify({
            "success": True,
            "message": "OCR处理成功",
            "data": ocr_results
        }), 200

    except Exception as e:
        logger.error(f"OCR处理失败: {e}")
        return jsonify({
            "error": "服务器内部错误",
            "message": str(e)
        }), 500

@ocr_bp.route('/results', methods=['GET'])
def get_ocr_results():
    """
    获取历史OCR结果
    ---
    tags:
      - OCR服务
    parameters:
      - in: query
        name: page
        type: integer
        required: false
        default: 1
        description: 页码
      - in: query
        name: per_page
        type: integer
        required: false
        default: 20
        description: 每页结果数
      - in: query
        name: min_confidence
        type: number
        required: false
        default: 0.0
        description: 最小置信度阈值
    responses:
      200:
        description: 成功获取结果
      500:
        description: 服务器内部错误
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        min_confidence = float(request.args.get('min_confidence', 0.0))

        # 构建查询
        query = OCRResult.query

        if min_confidence > 0:
            query = query.filter(OCRResult.confidence >= min_confidence)

        # 按时间降序排列并分页
        results = query.order_by(OCRResult.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "success": True,
            "data": {
                "items": [result.to_dict() for result in results.items],
                "total": results.total,
                "pages": results.pages,
                "current_page": page,
                "per_page": per_page
            }
        }), 200

    except Exception as e:
        logger.error(f"获取OCR结果失败: {e}")
        return jsonify({
            "error": "服务器内部错误",
            "message": str(e)
        }), 500


@ocr_bp.route('/results/<int:result_id>', methods=['GET'])
def get_single_result(result_id: int):
    """
    获取单个OCR结果
    ---
    tags:
      - OCR服务
    parameters:
      - in: path
        name: result_id
        type: integer
        required: true
        description: OCR结果ID
    responses:
      200:
        description: 成功获取结果
      404:
        description: 结果未找到
      500:
        description: 服务器内部错误
    """
    try:
        result = OCRResult.query.get_or_404(result_id)
        return jsonify({
            "success": True,
            "data": result.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"获取单个OCR结果失败: {e}")
        return jsonify({
            "error": "结果未找到",
            "message": str(e)
        }), 404


@ocr_bp.route('/performance', methods=['GET'])
def get_performance():
    """
    获取OCR服务性能指标
    ---
    tags:
      - OCR服务
    responses:
      200:
        description: 成功获取性能指标
    """
    try:
        metrics = ocr_service.get_performance_metrics()
        return jsonify({
            "success": True,
            "data": metrics
        }), 200

    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        return jsonify({
            "error": "获取性能指标失败",
            "message": str(e)
        }), 500


@ocr_bp.route('/batch-process', methods=['POST'])
def batch_process_images():
    """
    批量处理多个图像
    ---
    tags:
      - OCR服务
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: files
        type: file
        required: true
        description: 要处理的多个图像文件
    responses:
      200:
        description: 批量处理成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    if 'files' not in request.files:
        return jsonify({"error": "没有文件部分"}), 400

    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({"error": "未选择文件"}), 400

    results = []
    for file in files:
        if file and allowed_file(file.filename):
            try:
                # 保存临时文件
                filename = secure_filename(file.filename)
                temp_dir = current_app.config.get('UPLOAD_FOLDER', '/tmp')
                os.makedirs(temp_dir, exist_ok=True)

                input_path = os.path.join(temp_dir, filename)
                file.save(input_path)

                # 处理图像
                ocr_result = ocr_service.process_image(input_path, save_to_db=True)

                # 清理临时文件
                if os.path.exists(input_path):
                    os.remove(input_path)

                results.append({
                    "filename": filename,
                    "success": "error" not in ocr_result,
                    "result": ocr_result
                })

            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })

    return jsonify({
        "success": True,
        "message": "批量处理完成",
        "data": results
    }), 200
