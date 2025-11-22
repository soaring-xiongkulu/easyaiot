"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# 时区设置
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def beijing_now():
    """获取当前北京时间（无时区信息的datetime对象，用于数据库存储）"""
    beijing_dt = datetime.now(BEIJING_TZ)
    # 返回无时区信息的datetime对象，因为数据库字段不支持时区
    return beijing_dt.replace(tzinfo=None)

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    model_path = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500))
    version = db.Column(db.String(20), default="V1.0.0")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 导出模型路径字段
    onnx_model_path = db.Column(db.String(500))
    torchscript_model_path = db.Column(db.String(500))
    tensorrt_model_path = db.Column(db.String(500))
    openvino_model_path = db.Column(db.String(500))

    # 关系定义
    train_tasks = db.relationship(
        'TrainTask',
        foreign_keys='TrainTask.model_id',
        backref=db.backref('model_obj', lazy=True),  # 修改反向引用名称以避免冲突
        lazy='dynamic'
    )
    export_records = db.relationship('ExportRecord', back_populates='model', cascade='all, delete-orphan')

class TrainTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=True)
    progress = db.Column(db.Integer, default=0)
    dataset_path = db.Column(db.String(200), nullable=False)
    hyperparameters = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='running')
    train_log = db.Column(db.Text, nullable=False)
    checkpoint_dir = db.Column(db.String(500), nullable=False)
    metrics_path = db.Column(db.Text)
    minio_model_path = db.Column(db.String(500))
    train_results_path = db.Column(db.String(500))

class ExportRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    model_name = db.Column(db.String(100))  # 模型名称
    format = db.Column(db.String(50), nullable=False)
    minio_path = db.Column(db.String(500))
    local_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=beijing_now)  # 使用北京时间
    status = db.Column(db.String(20), default='PENDING')  # 新增状态字段
    message = db.Column(db.Text)  # 新增错误信息字段
    model = db.relationship('Model', back_populates='export_records')

class InferenceTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=True)
    inference_type = db.Column(db.String(20), nullable=False)  # image/video/rtsp
    input_source = db.Column(db.String(500))  # 原始文件路径或RTSP地址
    output_path = db.Column(db.String(500))  # 处理后文件在Minio的路径
    processed_frames = db.Column(db.Integer)  # 视频/流处理帧数
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='PROCESSING')  # PROCESSING/COMPLETED/FAILED
    error_message = db.Column(db.Text)
    processing_time = db.Column(db.Float)  # 单位：秒
    stream_output_url = db.Column(db.String(500))

class LLMConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 配置名称
    description = db.Column(db.Text)  # 配置描述
    model_type = db.Column(db.String(50), default="text")  # 模型类型: text, vision, audio, multimodal
    icon_url = db.Column(db.String(500))  # 模型图标/图片URL
    vendor = db.Column(db.String(100))  # 模型供应商 (e.g., OpenAI, Anthropic)
    base_url = db.Column(db.String(500), nullable=False)  # API基础URL
    api_key = db.Column(db.String(200), nullable=False)  # API密钥
    model = db.Column(db.String(100), nullable=False)  # 模型名称
    api_version = db.Column(db.String(50))  # API版本
    request_timeout = db.Column(db.Integer, default=30)  # 请求超时时间(秒)
    max_retries = db.Column(db.Integer, default=3)  # 最大重试次数
    context_window = db.Column(db.Integer)  # 上下文窗口大小
    max_output_tokens = db.Column(db.Integer)  # 单次请求最大输出Token数
    supported_features = db.Column(db.JSON)  # 支持的功能列表 (e.g., ['function_call', 'json_mode'])
    temperature = db.Column(db.Float, default=0.7)  # 默认温度
    system_prompt = db.Column(db.Text)  # 默认系统提示词
    is_customizable = db.Column(db.Boolean, default=False)  # 是否支持微调
    rag_enabled = db.Column(db.Boolean, default=False)  # 是否启用RAG
    prompt_template = db.Column(db.Text)  # 预定义提示词模板
    domain_adaptation = db.Column(db.String(100), default="general")  # 领域适配 (e.g., general, legal, financial)
    input_token_price = db.Column(db.Float, default=0.0)  # 输入Token单价(RMB)
    output_token_price = db.Column(db.Float, default=0.0)  # 输出Token单价(RMB)
    avg_response_time = db.Column(db.Float)  # 平均响应时间(毫秒)
    total_tokens_used = db.Column(db.BigInteger, default=0)  # 累计使用Token数
    monthly_budget = db.Column(db.Float)  # 月度预算(RMB)
    is_active = db.Column(db.Boolean, default=False)  # 是否为当前激活配置
    status = db.Column(db.String(20), default='testing')  # 状态: active, disabled, testing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_test_time = db.Column(db.DateTime)  # 最后一次测试时间

class OCRResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)  # 识别出的文本
    confidence = db.Column(db.Float)  # 置信度
    bbox = db.Column(db.JSON)  # 边界框坐标 [x1, y1, x2, y2]
    polygon = db.Column(db.JSON)  # 多边形坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    page_num = db.Column(db.Integer, default=1)  # 页码
    line_num = db.Column(db.Integer)  # 行号
    word_num = db.Column(db.Integer)  # 单词序号
    image_url = db.Column(db.String(500))  # 新增：图片在OSS中的URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox,
            'polygon': self.polygon,
            'page_num': self.page_num,
            'line_num': self.line_num,
            'word_num': self.word_num,
            'image_url': self.image_url,  # 新增
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SpeechRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), unique=True, nullable=False)  # 订单ID
    audio_file_path = db.Column(db.String(500))  # 音频文件在Minio的路径
    filename = db.Column(db.String(255), nullable=False)  # 原始文件名
    file_size = db.Column(db.Integer, nullable=False)  # 文件大小(字节)
    duration = db.Column(db.Integer, nullable=False)  # 音频时长(秒)
    recognized_text = db.Column(db.Text)  # 识别出的文本
    confidence = db.Column(db.Float)  # 整体置信度
    status = db.Column(db.String(20), default='UPLOADED')  # 状态: UPLOADED/PROCESSING/COMPLETED/FAILED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    completed_at = db.Column(db.DateTime)  # 完成时间
    error_message = db.Column(db.Text)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'duration': self.duration,
            'recognized_text': self.recognized_text,
            'confidence': self.confidence,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

    def __repr__(self):
        return f'<SpeechRecord {self.filename} ({self.status})>'


class AIService(db.Model):
    """AI服务表，用于维护所有部署的AI服务"""
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=True)  # 关联的模型ID（可空，支持心跳自动创建）
    service_name = db.Column(db.String(100), nullable=False)  # 服务名称（允许重复，支持同一服务名称的多个实例）
    server_ip = db.Column(db.String(50))  # 部署的服务器IP
    port = db.Column(db.Integer)  # 服务端口
    inference_endpoint = db.Column(db.String(200))  # 推理接口地址
    status = db.Column(db.String(20), default='stopped')  # 状态: running/stopped/error
    mac_address = db.Column(db.String(50))  # MAC地址
    deploy_time = db.Column(db.DateTime, default=beijing_now)  # 部署时间
    last_heartbeat = db.Column(db.DateTime)  # 最后上报时间
    process_id = db.Column(db.Integer)  # 进程ID
    log_path = db.Column(db.String(500))  # 日志文件路径
    model_version = db.Column(db.String(20))  # 模型版本号
    format = db.Column(db.String(50))  # 模型格式 (onnx, openvino, pytorch等)
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)
    
    # 关系定义
    model = db.relationship('Model', backref=db.backref('ai_services', lazy='dynamic'))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'service_name': self.service_name,
            'server_ip': self.server_ip,
            'port': self.port,
            'inference_endpoint': self.inference_endpoint,
            'status': self.status,
            'mac_address': self.mac_address,
            'deploy_time': self.deploy_time.isoformat() if self.deploy_time else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'process_id': self.process_id,
            'log_path': self.log_path,
            'model_version': self.model_version,
            'format': self.format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AIService {self.service_name} ({self.status})>'

