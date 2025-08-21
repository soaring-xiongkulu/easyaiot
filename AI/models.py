from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    model_path = db.Column(db.String(500), nullable=True)  # 原始模型路径
    training_record_id = db.Column(
        db.Integer,
        db.ForeignKey('training_record.id', ondelete="SET NULL"),
        nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 导出模型路径字段（每个类型一个地址）
    onnx_model_path = db.Column(db.String(500))  # ONNX格式路径
    torchscript_model_path = db.Column(db.String(500))  # TorchScript格式路径
    tensorrt_model_path = db.Column(db.String(500))  # TensorRT格式路径
    openvino_model_path = db.Column(db.String(500))  # OpenVINO格式路径

    # 关系定义
    training_records = db.relationship('TrainingRecord', backref='model', lazy=True)
    export_records = db.relationship('ExportRecord', back_populates='model', cascade='all, delete-orphan')


class TrainingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    dataset_path = db.Column(db.String(200), nullable=False)
    hyperparameters = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='running')
    train_log = db.Column(db.String(500), nullable=False)
    checkpoint_dir = db.Column(db.String(500), nullable=False)
    metrics_path = db.Column(db.Text)
    minio_model_path = db.Column(db.String(500))  # Minio存储路径


class ExportRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    format = db.Column(db.String(50), nullable=False)  # 导出格式
    minio_path = db.Column(db.String(500))  # Minio存储路径（新增）
    local_path = db.Column(db.String(500))  # 本地缓存路径（可选）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    model = db.relationship('Model', back_populates='export_records')