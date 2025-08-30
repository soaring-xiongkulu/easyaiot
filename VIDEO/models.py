from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Device(db.Model):
    id = db.Column(db.String(100), primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    source = db.Column(db.Text, nullable=False)
    rtmp_stream = db.Column(db.Text, nullable=False)
    http_stream = db.Column(db.Text, nullable=False)
    stream = db.Column(db.SmallInteger, nullable=True)
    ip = db.Column(db.String(45), nullable=True)
    port = db.Column(db.SMALLINT, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    mac = db.Column(db.String(17), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    firmware_version = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    hardware_id = db.Column(db.String(100), nullable=True)
    support_move = db.Column(db.Boolean, nullable=True)
    support_zoom = db.Column(db.Boolean, nullable=True)
    nvr_id = db.Column(db.Integer, db.ForeignKey('nvr.id', ondelete='CASCADE'), nullable=True)
    nvr_channel = db.Column(db.SmallInteger, nullable=True)
    images = db.relationship('Image', backref='project', lazy=True, cascade='all, delete-orphan')

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dataset_type = db.Column(db.String(50), default='unassigned')
    project_id = db.Column(db.String(100), db.ForeignKey('device.id'), nullable=False)
    annotations = db.relationship('Annotation', backref='image', lazy=True, cascade='all, delete-orphan')

class Nvr(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
