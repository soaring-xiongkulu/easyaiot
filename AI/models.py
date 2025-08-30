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
    rknn_model_path = db.Column(db.String(500))

    # 关系定义
    inference_tasks = db.relationship(
        'InferenceTask',
        foreign_keys='InferenceTask.model_id',
        backref=db.backref('model', lazy=True),
        lazy='dynamic'
    )
    export_records = db.relationship('ExportRecord', back_populates='model', cascade='all, delete-orphan')

class InferenceTask(db.Model):
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


class InferenceRecord(db.Model):
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
    # 与Model关系
    model = db.relationship('Model', backref=db.backref('inference_records', lazy=True))
    # 新增推流地址字段
    stream_output_url = db.Column(db.String(500))