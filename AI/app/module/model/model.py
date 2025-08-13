from datetime import datetime

from app.base.ext import db, BaseModel

@BaseModel.Scope(
    information=BaseModel.ScopeType.JSON,
    time=BaseModel.ScopeType.DATETIME
)
class Model(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    model_path = db.Column(db.String(500))
    last_trained = db.Column(db.DateTime)
    last_error = db.Column(db.Text)

    # 关联关系
    export_records = db.relationship('ExportRecord', back_populates='model', lazy=True, cascade='all, delete-orphan')


@BaseModel.Scope(
    information=BaseModel.ScopeType.JSON,
    time=BaseModel.ScopeType.DATETIME
)
class ExportRecord(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    format = db.Column(db.String(50), nullable=False)  # 导出格式 (onnx, torchscript等)
    path = db.Column(db.String(500), nullable=False)  # 导出文件路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    model = db.relationship('Model', back_populates='export_records')
