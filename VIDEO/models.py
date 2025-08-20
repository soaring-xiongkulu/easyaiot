from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    dataset_type = db.Column(db.String(20), default='unassigned')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    annotations = db.relationship('Annotation', backref='image', lazy=True, cascade='all, delete-orphan')
