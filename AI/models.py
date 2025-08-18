from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    images = db.relationship('Image', backref='project', lazy=True, cascade='all, delete-orphan')
    labels = db.relationship('Label', backref='project', lazy=True, cascade='all, delete-orphan')
    export_records = db.relationship('ExportRecord', back_populates='project', lazy=True, cascade='all, delete-orphan')


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    original_filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dataset_type = db.Column(db.String(20), default='unassigned')  # train, val, test, unassigned

    # 外键
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    # 关联关系
    annotations = db.relationship('Annotation', backref='image', lazy=True, cascade='all, delete-orphan')


class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#0066ff')  # HEX颜色代码
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    # 关联关系
    annotations = db.relationship('Annotation', backref='label', lazy=True)


class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    label_id = db.Column(db.Integer, db.ForeignKey('label.id'), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)


# 导出记录模型
class ExportRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    format = db.Column(db.String(50), nullable=False)  # 导出格式 (onnx, torchscript等)
    path = db.Column(db.String(500), nullable=False)  # 导出文件路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    project = db.relationship('Project', back_populates='export_records')