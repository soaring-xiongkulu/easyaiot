from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
    format = db.Column(db.String(50), nullable=False)
    minio_path = db.Column(db.String(500))
    local_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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