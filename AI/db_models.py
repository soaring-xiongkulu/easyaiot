"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
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
    version = db.Column(db.String(20), default="1.0.0")
    # 0=未部署 1=已部署 2=训练中 3=已下线（与前端模型管理一致）
    status = db.Column(db.Integer, default=0, nullable=False)
    # 模型支持的全部识别标签（JSON 数组）；推理时可从中选择子集
    class_names = db.Column(db.Text, nullable=True)
    # 默认启用的识别标签（JSON 数组，为空时表示启用全部 class_names）
    selected_class_names = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 导出模型路径字段
    onnx_model_path = db.Column(db.String(500))
    torchscript_model_path = db.Column(db.String(500))
    tensorrt_model_path = db.Column(db.String(500))
    openvino_model_path = db.Column(db.String(500))
    # 模型来源：upload | auto_label | smart_label | train | import
    model_origin = db.Column(db.String(32), default='upload', nullable=True)
    # 来源引用，如 dataset:15 / train_task:88
    origin_ref = db.Column(db.String(128), nullable=True)

    export_records = db.relationship('ExportRecord', back_populates='model', cascade='all, delete-orphan')

class TrainTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    model_id = db.Column(db.Integer, nullable=True)  # 已废弃，保留列兼容历史数据
    progress = db.Column(db.Integer, default=0)
    dataset_path = db.Column(db.String(200), nullable=False)
    dataset_name = db.Column(db.String(100), nullable=True)
    dataset_version = db.Column(db.String(100), nullable=True)
    hyperparameters = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='running')
    train_log = db.Column(db.Text, nullable=False)
    checkpoint_dir = db.Column(db.String(500), nullable=False)
    metrics_path = db.Column(db.Text)
    minio_model_path = db.Column(db.String(500))
    train_results_path = db.Column(db.String(500))
    schedule_policy = db.Column(db.String(20), default='auto', nullable=True,
                               comment='调度策略: auto/node（local 已废弃，兼容旧数据）')
    target_node_id = db.Column(db.BigInteger, nullable=True, comment='指定部署节点ID')
    node_id = db.Column(db.BigInteger, nullable=True, comment='实际运行节点ID')
    service_server_ip = db.Column(db.String(128), nullable=True, comment='实际运行节点 IP/主机')
    service_process_id = db.Column(db.BigInteger, nullable=True, comment='远程 Worker PID')

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


class PlateAlgorithmVersion(db.Model):
    """车牌算法版本表（独立于通用模型管理）"""
    __tablename__ = 'plate_algorithm_version'

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    base_model = db.Column(db.String(100), nullable=False, default='yolo11n.pt')
    model_path = db.Column(db.String(500), nullable=True)  # MinIO下载URL
    metrics_path = db.Column(db.String(500), nullable=True)  # 训练曲线CSV
    train_results_path = db.Column(db.String(500), nullable=True)  # 训练结果图
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft/active/archived
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)

    train_tasks = db.relationship(
        'PlateTrainTask',
        backref=db.backref('version_obj', lazy=True),
        lazy='dynamic'
    )
    inference_tasks = db.relationship(
        'PlateInferenceTask',
        backref=db.backref('version_obj', lazy=True),
        lazy='dynamic'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'description': self.description,
            'base_model': self.base_model,
            'model_path': self.model_path,
            'metrics_path': self.metrics_path,
            'train_results_path': self.train_results_path,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlateDataset(db.Model):
    """车牌训练数据集表（独立管理）"""
    __tablename__ = 'plate_dataset'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    dataset_source = db.Column(db.String(1000), nullable=False)  # 本地目录/zip 或 MinIO下载URL
    source_type = db.Column(db.String(20), nullable=False, default='custom')  # custom/merged
    status = db.Column(db.String(20), nullable=False, default='ready')  # ready/archived
    merged_from = db.Column(db.Text, nullable=True)  # JSON字符串，记录合并来源数据集ID列表
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)

    def to_dict(self):
        merged_from = []
        if self.merged_from:
            try:
                merged_from = json.loads(self.merged_from)
            except Exception:
                merged_from = []

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'dataset_source': self.dataset_source,
            'source_type': self.source_type,
            'status': self.status,
            'merged_from': merged_from,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlateTrainTask(db.Model):
    """车牌算法训练任务表"""
    __tablename__ = 'plate_train_task'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('plate_algorithm_version.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='preparing')  # preparing/running/completed/stopped/failed
    progress = db.Column(db.Integer, nullable=False, default=0)
    dataset_source = db.Column(db.String(1000), nullable=False)
    dataset_local_path = db.Column(db.String(1000), nullable=True)
    normalized_data_yaml = db.Column(db.String(1000), nullable=True)
    hyperparameters = db.Column(db.Text, nullable=True)
    train_log = db.Column(db.Text, nullable=False, default='')
    error_message = db.Column(db.Text, nullable=True)
    minio_model_path = db.Column(db.String(500), nullable=True)
    metrics_path = db.Column(db.String(500), nullable=True)
    train_results_path = db.Column(db.String(500), nullable=True)
    start_time = db.Column(db.DateTime, default=beijing_now)
    end_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)

    def to_dict(self):
        dataset_id = None
        dataset_name = None
        if self.hyperparameters:
            try:
                hp = json.loads(self.hyperparameters)
                dataset_id = hp.get('dataset_id')
                dataset_name = hp.get('dataset_name')
            except Exception:
                dataset_id = None
                dataset_name = None

        return {
            'id': self.id,
            'version_id': self.version_id,
            'status': self.status,
            'progress': self.progress,
            'dataset_id': dataset_id,
            'dataset_name': dataset_name,
            'dataset_source': self.dataset_source,
            'dataset_local_path': self.dataset_local_path,
            'normalized_data_yaml': self.normalized_data_yaml,
            'hyperparameters': self.hyperparameters,
            'train_log': self.train_log,
            'error_message': self.error_message,
            'minio_model_path': self.minio_model_path,
            'metrics_path': self.metrics_path,
            'train_results_path': self.train_results_path,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlateInferenceTask(db.Model):
    """车牌算法推理任务表"""
    __tablename__ = 'plate_inference_task'

    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('plate_algorithm_version.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='processing')  # processing/completed/failed
    input_source = db.Column(db.String(1000), nullable=True)
    output_image_path = db.Column(db.String(500), nullable=True)
    output_json_path = db.Column(db.String(500), nullable=True)
    detection_count = db.Column(db.Integer, nullable=False, default=0)
    result_preview = db.Column(db.Text, nullable=True)  # JSON字符串，保存部分检测结果
    error_message = db.Column(db.Text, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)

    def to_dict(self):
        return {
            'id': self.id,
            'version_id': self.version_id,
            'status': self.status,
            'input_source': self.input_source,
            'output_image_path': self.output_image_path,
            'output_json_path': self.output_json_path,
            'detection_count': self.detection_count,
            'result_preview': self.result_preview,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class LLMModel(db.Model):
    """大模型配置表（简化版）"""
    __tablename__ = 'llm_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='模型名称')
    service_type = db.Column(db.String(20), default='online', nullable=False, comment='服务类型[online:线上服务,local:本地服务]')
    vendor = db.Column(db.String(50), nullable=False, comment='供应商[aliyun:阿里云,openai:OpenAI,anthropic:Anthropic,local:本地服务]')
    model_type = db.Column(db.String(50), default='vision', nullable=False, comment='模型类型[text:文本,vision:视觉,multimodal:多模态]')
    model_name = db.Column(db.String(100), nullable=False, comment='模型标识（如qwen-vl-max）')
    base_url = db.Column(db.String(500), nullable=False, comment='API基础URL')
    api_key = db.Column(db.String(200), nullable=True, comment='API密钥（线上服务必填，本地服务可选）')
    api_version = db.Column(db.String(50), nullable=True, comment='API版本')
    
    # 基础配置
    temperature = db.Column(db.Float, default=0.7, nullable=False, comment='温度参数')
    max_tokens = db.Column(db.Integer, default=2000, nullable=False, comment='最大输出token数')
    timeout = db.Column(db.Integer, default=60, nullable=False, comment='请求超时时间（秒）')
    
    # 状态管理
    is_active = db.Column(db.Boolean, default=False, nullable=False, comment='是否激活')
    status = db.Column(db.String(20), default='inactive', nullable=False, comment='状态[active:激活,inactive:未激活,error:错误]')
    last_test_time = db.Column(db.DateTime, nullable=True, comment='最后测试时间')
    last_test_result = db.Column(db.Text, nullable=True, comment='最后测试结果')
    
    # 描述信息
    description = db.Column(db.Text, nullable=True, comment='模型描述')
    icon_url = db.Column(db.String(500), nullable=True, comment='图标URL')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'service_type': self.service_type,
            'vendor': self.vendor,
            'model_type': self.model_type,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'api_key': self.api_key[:10] + '***' if self.api_key else None,  # 只显示前10位
            'api_version': self.api_version,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'is_active': self.is_active,
            'status': self.status,
            'last_test_time': self.last_test_time.isoformat() if self.last_test_time else None,
            'last_test_result': self.last_test_result,
            'description': self.description,
            'icon_url': self.icon_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


rag_knowledge_set_segment = db.Table(
    'rag_knowledge_set_segment',
    db.Column('knowledge_set_id', db.Integer, db.ForeignKey('rag_knowledge_set.id', ondelete='CASCADE'), primary_key=True),
    db.Column('segment_id', db.Integer, db.ForeignKey('rag_knowledge_segment.id', ondelete='CASCADE'), primary_key=True),
)

rag_expert_knowledge_set = db.Table(
    'rag_expert_knowledge_set',
    db.Column('expert_id', db.Integer, db.ForeignKey('rag_expert.id', ondelete='CASCADE'), primary_key=True),
    db.Column('knowledge_set_id', db.Integer, db.ForeignKey('rag_knowledge_set.id', ondelete='CASCADE'), primary_key=True),
)


class RagKnowledgeDocument(db.Model):
    """知识来源文档；与知识集解耦，可解析为多个可审核片段。"""
    __tablename__ = 'rag_knowledge_document'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(80))
    char_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='parsed', nullable=False)
    source_type = db.Column(db.String(20), default='upload', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    segments = db.relationship('RagKnowledgeSegment', backref='document', cascade='all, delete-orphan')

    def to_dict(self):
        enabled = sum(1 for item in self.segments if item.is_enabled)
        return {'id': self.id, 'name': self.name, 'content_type': self.content_type,
                'char_count': self.char_count, 'status': self.status, 'source_type': self.source_type,
                'segment_count': len(self.segments), 'enabled_segment_count': enabled,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None}


class RagKnowledgeSegment(db.Model):
    """可追溯、可编辑、可复用的最小知识单元。"""
    __tablename__ = 'rag_knowledge_segment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey('rag_knowledge_document.id'), nullable=False, index=True)
    segment_index = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    search_terms = db.Column(db.Text, nullable=False, default='')
    tags = db.Column(db.JSON, default=list)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    milvus_id = db.Column(db.String(64), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'document_id': self.document_id, 'document_name': self.document.name,
                'index': self.segment_index, 'title': self.title or f'片段 {self.segment_index + 1}',
                'content': self.content, 'tags': self.tags or [], 'is_enabled': self.is_enabled,
                'knowledge_set_count': len(self.knowledge_sets),
                'updated_at': self.updated_at.isoformat() if self.updated_at else None}


class RagKnowledgeSet(db.Model):
    """跨文档组合知识片段的可复用业务知识资产。"""
    __tablename__ = 'rag_knowledge_set'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    segments = db.relationship('RagKnowledgeSegment', secondary=rag_knowledge_set_segment, backref='knowledge_sets')

    def to_dict(self):
        documents = {item.document_id for item in self.segments}
        return {'id': self.id, 'name': self.name, 'category': self.category,
                'description': self.description, 'segment_ids': [item.id for item in self.segments],
                'segment_count': len(self.segments), 'document_count': len(documents),
                'expert_count': len(self.experts),
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None}


class RagExpert(db.Model):
    """组合多个知识集的 RAG 应用专家。"""
    __tablename__ = 'rag_expert'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    system_prompt = db.Column(db.Text, nullable=False)
    welcome_message = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    knowledge_sets = db.relationship('RagKnowledgeSet', secondary=rag_expert_knowledge_set, backref='experts')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'category': self.category,
                'knowledge_set_ids': [item.id for item in self.knowledge_sets],
                'knowledge_set_names': [item.name for item in self.knowledge_sets],
                'system_prompt': self.system_prompt, 'welcome_message': self.welcome_message,
                'is_enabled': self.is_enabled,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None}

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
    node_id = db.Column(db.BigInteger)  # 部署所在服务器节点 ID（iot-node）
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
            'node_id': self.node_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AIService {self.service_name} ({self.status})>'


class LLMDeployService(db.Model):
    """GPU 节点大模型部署实例（Qwen / vLLM）"""
    __tablename__ = 'llm_deploy_service'

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    qwen_model_key = db.Column(db.String(50), nullable=False)
    hf_model_id = db.Column(db.String(200), nullable=False)
    node_id = db.Column(db.BigInteger)
    server_ip = db.Column(db.String(50))
    port = db.Column(db.Integer)
    api_endpoint = db.Column(db.String(300))
    tensor_parallel_size = db.Column(db.Integer, default=1)
    max_model_len = db.Column(db.Integer, default=8192)
    status = db.Column(db.String(20), default='deploying')
    llm_config_id = db.Column(db.Integer, db.ForeignKey('llm_config.id'), nullable=True)
    process_id = db.Column(db.Integer)
    log_path = db.Column(db.String(500))
    error_message = db.Column(db.Text)
    deploy_time = db.Column(db.DateTime, default=beijing_now)
    last_heartbeat = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)

    llm_config = db.relationship('LLMModel', backref=db.backref('deploy_services', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'service_name': self.service_name,
            'qwen_model_key': self.qwen_model_key,
            'hf_model_id': self.hf_model_id,
            'node_id': self.node_id,
            'server_ip': self.server_ip,
            'port': self.port,
            'api_endpoint': self.api_endpoint,
            'tensor_parallel_size': self.tensor_parallel_size,
            'max_model_len': self.max_model_len,
            'status': self.status,
            'llm_config_id': self.llm_config_id,
            'process_id': self.process_id,
            'log_path': self.log_path,
            'error_message': self.error_message,
            'deploy_time': self.deploy_time.isoformat() if self.deploy_time else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class SAMInferenceResult(db.Model):
    """SAM 分割推理结果表"""
    __tablename__ = 'sam_inference_result'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prompt_type = db.Column(db.String(20), nullable=False, comment='提示类型[point/box/auto/text]')
    prompt_data = db.Column(db.Text, nullable=True, comment='提示参数JSON')
    image_url = db.Column(db.String(500), nullable=True, comment='图片URL')
    result_data = db.Column(db.Text, nullable=True, comment='推理结果JSON')
    model_type = db.Column(db.String(20), nullable=True, comment='模型类型[vit_b/vit_l/vit_h]')
    inference_ms = db.Column(db.Integer, nullable=True, comment='推理耗时(毫秒)')
    created_at = db.Column(db.DateTime, default=beijing_now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'prompt_type': self.prompt_type,
            'prompt_data': self.prompt_data,
            'image_url': self.image_url,
            'result_data': self.result_data,
            'model_type': self.model_type,
            'inference_ms': self.inference_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AutoLabelTask(db.Model):
    """自动化标注任务表"""
    __tablename__ = 'auto_label_task'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.BigInteger, nullable=False, comment='数据集ID')
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=True, comment='模型ID（直连推理，无需部署服务）')
    model_service_id = db.Column(db.Integer, db.ForeignKey('ai_service.id'), nullable=True, comment='AI服务ID（兼容旧版）')
    status = db.Column(db.String(20), default='PENDING', nullable=False, comment='状态[PENDING:待处理,PROCESSING:处理中,COMPLETED:已完成,FAILED:失败]')
    total_images = db.Column(db.Integer, default=0, comment='总图片数')
    processed_images = db.Column(db.Integer, default=0, comment='已处理图片数')
    success_count = db.Column(db.Integer, default=0, comment='成功标注数')
    failed_count = db.Column(db.Integer, default=0, comment='失败数')
    confidence_threshold = db.Column(db.Float, default=0.5, comment='置信度阈值')
    label_mode = db.Column(db.String(20), default='yolo', comment='标注模式[yolo/sam]')
    text_prompts = db.Column(db.Text, nullable=True, comment='SAM 文本 prompt JSON 数组')
    annotation_type = db.Column(db.String(20), default='rectangle', comment='标注形态[rectangle/polygon]')
    phase = db.Column(db.String(20), nullable=True, comment='阶段[BOOTSTRAP/PRODUCTION]')
    bootstrap_limit = db.Column(db.Integer, nullable=True, comment='冷启动张数上限')
    bootstrap_selection = db.Column(db.String(30), default='unlabeled_first', comment='冷启动选图策略')
    review_passed = db.Column(db.Boolean, default=False, comment='人工抽检是否通过')
    return_masks = db.Column(db.Boolean, default=False, comment='SAM 是否返回 mask')
    pipeline_config = db.Column(db.Text, nullable=True, comment='无人值守流水线配置 JSON')
    execution_mode = db.Column(db.String(20), default='local', comment='执行模式[local/cluster]')
    queue_priority = db.Column(db.Integer, default=0, comment='队列优先级，越大越优先')
    selected_frame_task_ids = db.Column(db.Text, nullable=True, comment='选中的帧捕获任务 ID JSON 数组')
    created_at = db.Column(db.DateTime, default=beijing_now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now, comment='更新时间')
    started_at = db.Column(db.DateTime, nullable=True, comment='开始时间')
    completed_at = db.Column(db.DateTime, nullable=True, comment='完成时间')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    
    # 关系定义
    model = db.relationship('Model', backref=db.backref('auto_label_tasks', lazy='dynamic'))
    model_service = db.relationship('AIService', backref=db.backref('auto_label_tasks', lazy='dynamic'))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'model_id': self.model_id,
            'model_service_id': self.model_service_id,
            'status': self.status,
            'total_images': self.total_images,
            'processed_images': self.processed_images,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'confidence_threshold': self.confidence_threshold,
            'label_mode': self.label_mode or 'yolo',
            'text_prompts': json.loads(self.text_prompts) if self.text_prompts else None,
            'annotation_type': self.annotation_type or 'rectangle',
            'phase': self.phase,
            'bootstrap_limit': self.bootstrap_limit,
            'bootstrap_selection': self.bootstrap_selection,
            'review_passed': self.review_passed,
            'return_masks': self.return_masks,
            'pipeline_config': json.loads(self.pipeline_config) if self.pipeline_config else None,
            'execution_mode': self.execution_mode or 'local',
            'queue_priority': self.queue_priority or 0,
            'selected_frame_task_ids': json.loads(self.selected_frame_task_ids) if self.selected_frame_task_ids else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }
    
    def __repr__(self):
        return f'<AutoLabelTask {self.id} ({self.status})>'


class AutoLabelSubTask(db.Model):
    """自动标注子任务（按摄像头/分片排队，可调度到集群节点）"""
    __tablename__ = 'auto_label_subtask'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_task_id = db.Column(db.Integer, db.ForeignKey('auto_label_task.id'), nullable=False, comment='父任务ID')
    dataset_id = db.Column(db.BigInteger, nullable=False, comment='数据集ID')
    frame_task_id = db.Column(db.BigInteger, nullable=True, comment='帧捕获任务/摄像头ID')
    frame_task_name = db.Column(db.String(200), nullable=True, comment='摄像头任务名称')
    rtmp_url = db.Column(db.Text, nullable=True, comment='视频流地址')
    subtask_type = db.Column(db.String(30), default='capture_label', comment='子任务类型')
    status = db.Column(
        db.String(20), default='QUEUED', nullable=False,
        comment='QUEUED/DISPATCHING/RUNNING/COMPLETED/FAILED',
    )
    queue_position = db.Column(db.Integer, default=0, comment='队列位置')
    assigned_node_id = db.Column(db.Integer, nullable=True, comment='分配的节点ID')
    assigned_node_host = db.Column(db.String(100), nullable=True, comment='节点主机')
    workload_id = db.Column(db.String(64), nullable=True, comment='节点工作负载绑定ID')
    captured_count = db.Column(db.Integer, default=0)
    labeled_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    processed_images = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    config_json = db.Column(db.Text, nullable=True, comment='子任务配置 JSON')
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    parent_task = db.relationship('AutoLabelTask', backref=db.backref('subtasks', lazy='dynamic'))

    def to_dict(self):
        cfg = {}
        if self.config_json:
            try:
                cfg = json.loads(self.config_json) if isinstance(self.config_json, str) else self.config_json
            except Exception:
                cfg = {}
        return {
            'id': self.id,
            'parent_task_id': self.parent_task_id,
            'dataset_id': self.dataset_id,
            'frame_task_id': self.frame_task_id,
            'frame_task_name': self.frame_task_name,
            'rtmp_url': self.rtmp_url,
            'subtask_type': self.subtask_type,
            'status': self.status,
            'queue_position': self.queue_position,
            'assigned_node_id': self.assigned_node_id,
            'assigned_node_host': self.assigned_node_host,
            'captured_count': self.captured_count,
            'labeled_count': self.labeled_count,
            'failed_count': self.failed_count,
            'processed_images': self.processed_images,
            'error_message': self.error_message,
            'config': cfg,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<AutoLabelSubTask {self.id} task={self.parent_task_id} ({self.status})>'


class AutoLabelResult(db.Model):
    """自动化标注结果表"""
    __tablename__ = 'auto_label_result'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('auto_label_task.id'), nullable=False, comment='任务ID')
    dataset_image_id = db.Column(db.BigInteger, nullable=False, comment='数据集图片ID')
    annotations = db.Column(db.Text, nullable=True, comment='标注结果JSON')
    status = db.Column(db.String(20), default='SUCCESS', nullable=False, comment='状态[SUCCESS:成功,FAILED:失败]')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    created_at = db.Column(db.DateTime, default=beijing_now, comment='创建时间')
    
    # 关系定义
    task = db.relationship('AutoLabelTask', backref=db.backref('results', lazy='dynamic'))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'dataset_image_id': self.dataset_image_id,
            'annotations': self.annotations,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AutoLabelResult {self.id} ({self.status})>'


class AutoLabelModelHistory(db.Model):
    """数据集自动标注模型更新历史（条数上限可配置，默认读环境变量）"""
    __tablename__ = 'auto_label_model_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.BigInteger, nullable=False, index=True, comment='数据集ID')
    model_id = db.Column(db.Integer, nullable=True, comment='发布后模型ID')
    train_task_id = db.Column(db.Integer, nullable=True, comment='训练任务ID')
    source_model_id = db.Column(db.Integer, nullable=True, comment='微调基座模型ID')
    version_no = db.Column(db.Integer, nullable=False, default=1, comment='更新序号')
    annotated_count = db.Column(db.Integer, default=0, comment='参与训练的已标注张数')
    class_names = db.Column(db.Text, nullable=True, comment='类别 JSON')
    map50 = db.Column(db.Float, nullable=True, comment='训练 mAP50')
    status = db.Column(
        db.String(20), default='PENDING', nullable=False,
        comment='PENDING/TRAINING/COMPLETED/FAILED',
    )
    trigger_source = db.Column(
        db.String(30), default='manual', nullable=False,
        comment='manual/pipeline',
    )
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=beijing_now, comment='创建时间')
    completed_at = db.Column(db.DateTime, nullable=True, comment='完成时间')

    def to_dict(self):
        import json as _json
        names = None
        if self.class_names:
            try:
                names = _json.loads(self.class_names)
            except Exception:
                names = self.class_names
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'model_id': self.model_id,
            'train_task_id': self.train_task_id,
            'source_model_id': self.source_model_id,
            'version_no': self.version_no,
            'annotated_count': self.annotated_count,
            'class_names': names,
            'map50': self.map50,
            'status': self.status,
            'trigger_source': self.trigger_source,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<AutoLabelModelHistory ds={self.dataset_id} v{self.version_no} ({self.status})>'


def ensure_train_task_name_column(engine):
    """老库 train_task 表无 name 列时补列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'train_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('train_task')}
        if 'name' not in col_names:
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE train_task ADD COLUMN name VARCHAR(100)'))
            log.info('已为 train_task 表添加 name 列')
    except Exception as e:
        log.warning('ensure_train_task_name_column: %s', e)


def ensure_train_task_dataset_columns(engine):
    """老库 train_task 表无 dataset_name / dataset_version 列时补列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'train_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('train_task')}
        with engine.begin() as conn:
            if 'dataset_name' not in col_names:
                conn.execute(text('ALTER TABLE train_task ADD COLUMN dataset_name VARCHAR(100)'))
                log.info('已为 train_task 表添加 dataset_name 列')
            if 'dataset_version' not in col_names:
                conn.execute(text('ALTER TABLE train_task ADD COLUMN dataset_version VARCHAR(100)'))
                log.info('已为 train_task 表添加 dataset_version 列')
    except Exception as e:
        log.warning('ensure_train_task_dataset_columns: %s', e)


def ensure_train_task_cluster_columns(engine):
    """老库 train_task 表补集群调度相关列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'schedule_policy': 'VARCHAR(20) DEFAULT \'local\'',
        'target_node_id': 'BIGINT',
        'node_id': 'BIGINT',
        'service_server_ip': 'VARCHAR(128)',
        'service_process_id': 'BIGINT',
    }
    try:
        inspector = inspect(engine)
        if 'train_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('train_task')}
        with engine.begin() as conn:
            for col, ddl in columns.items():
                if col not in col_names:
                    conn.execute(text(f'ALTER TABLE train_task ADD COLUMN {col} {ddl}'))
                    log.info('已为 train_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_train_task_cluster_columns: %s', e)


def ensure_model_class_columns(engine):
    """老库 model 表无 class_names / selected_class_names 列时补列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'model' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('model')}
        with engine.begin() as conn:
            if 'class_names' not in col_names:
                conn.execute(text('ALTER TABLE model ADD COLUMN class_names TEXT'))
                log.info('已为 model 表添加 class_names 列')
            if 'selected_class_names' not in col_names:
                conn.execute(text('ALTER TABLE model ADD COLUMN selected_class_names TEXT'))
                log.info('已为 model 表添加 selected_class_names 列')
    except Exception as e:
        log.warning('ensure_model_class_columns: %s', e)


def ensure_auto_label_task_model_id_column(engine):
    """老库 auto_label_task 表无 model_id 列时补列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'auto_label_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('auto_label_task')}
        if 'model_id' in col_names:
            return
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE auto_label_task ADD COLUMN model_id INTEGER'))
        log.info('已为 auto_label_task 表添加 model_id 列')
    except Exception as e:
        log.warning('ensure_auto_label_task_model_id_column: %s', e)


def ensure_auto_label_task_sam_columns(engine):
    """老库 auto_label_task 表补 SAM 相关列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'label_mode': "VARCHAR(20) DEFAULT 'yolo'",
        'text_prompts': 'TEXT',
        'annotation_type': "VARCHAR(20) DEFAULT 'rectangle'",
        'phase': 'VARCHAR(20)',
        'bootstrap_limit': 'INTEGER',
        'bootstrap_selection': "VARCHAR(30) DEFAULT 'unlabeled_first'",
        'review_passed': 'BOOLEAN DEFAULT FALSE',
        'return_masks': 'BOOLEAN DEFAULT FALSE',
    }
    try:
        inspector = inspect(engine)
        if 'auto_label_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('auto_label_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE auto_label_task ADD COLUMN {col} {ddl}'))
            log.info('已为 auto_label_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_auto_label_task_sam_columns: %s', e)


def ensure_auto_label_task_pipeline_column(engine):
    """老库 auto_label_task 表补 pipeline_config 列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'auto_label_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('auto_label_task')}
        if 'pipeline_config' in col_names:
            return
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE auto_label_task ADD COLUMN pipeline_config TEXT'))
        log.info('已为 auto_label_task 表添加 pipeline_config 列')
    except Exception as e:
        log.warning('ensure_auto_label_task_pipeline_column: %s', e)


def ensure_auto_label_task_cluster_columns(engine):
    """老库 auto_label_task 表补集群/队列相关列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'execution_mode': "VARCHAR(20) DEFAULT 'local'",
        'queue_priority': 'INTEGER DEFAULT 0',
        'selected_frame_task_ids': 'TEXT',
    }
    try:
        inspector = inspect(engine)
        if 'auto_label_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('auto_label_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE auto_label_task ADD COLUMN {col} {ddl}'))
            log.info('已为 auto_label_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_auto_label_task_cluster_columns: %s', e)


def ensure_auto_label_subtask_table(engine):
    """确保 auto_label_subtask 表存在。"""
    import logging
    from sqlalchemy import inspect

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'auto_label_subtask' in inspector.get_table_names():
            return
        AutoLabelSubTask.__table__.create(bind=engine, checkfirst=True)
        log.info('已创建 auto_label_subtask 表')
    except Exception as e:
        log.warning('ensure_auto_label_subtask_table: %s', e)


def ensure_auto_label_model_history_table(engine):
    """确保 auto_label_model_history 表存在。"""
    import logging
    from sqlalchemy import inspect

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'auto_label_model_history' in inspector.get_table_names():
            return
        AutoLabelModelHistory.__table__.create(bind=engine, checkfirst=True)
        log.info('已创建 auto_label_model_history 表')
    except Exception as e:
        log.warning('ensure_auto_label_model_history_table: %s', e)


def ensure_model_origin_columns(engine):
    """老库 model 表无 model_origin / origin_ref 列时补列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'model' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('model')}
        with engine.begin() as conn:
            if 'model_origin' not in col_names:
                conn.execute(text("ALTER TABLE model ADD COLUMN model_origin VARCHAR(32) DEFAULT 'upload'"))
                log.info('已为 model 表添加 model_origin 列')
            if 'origin_ref' not in col_names:
                conn.execute(text('ALTER TABLE model ADD COLUMN origin_ref VARCHAR(128)'))
                log.info('已为 model 表添加 origin_ref 列')
        backfill_model_origin(engine)
    except Exception as e:
        log.warning('ensure_model_origin_columns: %s', e)


def backfill_model_origin(engine):
    """根据名称/描述推断历史模型的 model_origin（仅填空值）。"""
    import logging
    from sqlalchemy import text

    log = logging.getLogger(__name__)
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE model SET model_origin = 'auto_label'
                WHERE (model_origin IS NULL OR model_origin = '' OR model_origin = 'upload')
                  AND (name ILIKE 'auto-label-%' OR description ILIKE '%自动标注%')
            """))
            conn.execute(text("""
                UPDATE model SET model_origin = 'smart_label'
                WHERE (model_origin IS NULL OR model_origin = '' OR model_origin = 'upload')
                  AND (description ILIKE '%智能标注%' OR description ILIKE '%sam_pipeline%'
                       OR description ILIKE '%sam 冷启动%')
            """))
            conn.execute(text("""
                UPDATE model SET model_origin = 'train'
                WHERE (model_origin IS NULL OR model_origin = '' OR model_origin = 'upload')
                  AND (description ILIKE '%训练任务%' OR description ILIKE '%train_task%'
                       OR description ILIKE '%从训练任务%')
            """))
        log.info('已尝试回填历史 model_origin')
    except Exception as e:
        log.warning('backfill_model_origin: %s', e)


def ensure_model_table_status_column(engine):
    """
    老库仅有 model 表但无 status 列时补列。
    SQLAlchemy create_all() 不会为已存在的表追加新列。
    """
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    try:
        inspector = inspect(engine)
        if 'model' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('model')}
        if 'status' in col_names:
            return
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE model ADD COLUMN status INTEGER DEFAULT 0'))
        log.info('已为 model 表添加 status 列')
    except Exception as e:
        log.warning('ensure_model_table_status_column: %s', e)
