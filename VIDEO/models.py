"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class DeviceDirectory(db.Model):
    """设备目录表，用于管理摄像头的目录结构"""
    __tablename__ = 'device_directory'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='目录名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('device_directory.id', ondelete='CASCADE'), nullable=True, comment='父目录ID，NULL表示根目录')
    description = db.Column(db.String(500), nullable=True, comment='目录描述')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序顺序')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 自关联关系：子目录
    children = db.relationship('DeviceDirectory', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade='all, delete-orphan')
    # 关联的设备
    devices = db.relationship('Device', backref='directory', lazy=True, cascade='all, delete-orphan')

class Device(db.Model):
    id = db.Column(db.String(100), primary_key=True)
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
    manufacturer = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    firmware_version = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(300), nullable=True)
    hardware_id = db.Column(db.String(100), nullable=True)
    support_move = db.Column(db.Boolean, nullable=True)
    support_zoom = db.Column(db.Boolean, nullable=True)
    nvr_id = db.Column(db.Integer, db.ForeignKey('nvr.id', ondelete='CASCADE'), nullable=True)
    nvr_channel = db.Column(db.SmallInteger, nullable=False)
    enable_forward = db.Column(db.Boolean, nullable=True)
    directory_id = db.Column(db.Integer, db.ForeignKey('device_directory.id', ondelete='SET NULL'), nullable=True, comment='所属目录ID')
    images = db.relationship('Image', backref='project', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    device_id = db.Column(db.String(100), db.ForeignKey('device.id'))  # 添加设备ID外键

class Nvr(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)

class Alert(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    object = db.Column(db.String(30), nullable=False)
    event = db.Column(db.String(30), nullable=False)
    region = db.Column(db.String(30), nullable=True)
    information = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text('NOW()'))
    device_id = db.Column(db.String(30), nullable=False)
    device_name = db.Column(db.String(30), nullable=False)
    image_path = db.Column(db.String(200), nullable=True)
    record_path = db.Column(db.String(200), nullable=True)


class SnapSpace(db.Model):
    """抓拍空间表"""
    __tablename__ = 'snap_space'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    space_name = db.Column(db.String(255), nullable=False, comment='空间名称')
    space_code = db.Column(db.String(255), nullable=False, unique=True, comment='空间编号（唯一标识）')
    bucket_name = db.Column(db.String(255), nullable=False, comment='MinIO bucket名称')
    save_mode = db.Column(db.SmallInteger, default=0, nullable=False, comment='文件保存模式[0:标准存储,1:归档存储]')
    save_time = db.Column(db.Integer, default=0, nullable=False, comment='文件保存时间[0:永久保存,>=7(单位:天)]')
    description = db.Column(db.String(500), nullable=True, comment='空间描述')
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='SET NULL'), nullable=True, unique=True, comment='关联的设备ID（一对一关系）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的抓拍任务
    snap_tasks = db.relationship('SnapTask', backref='snap_space', lazy=True, cascade='all, delete-orphan')
    # 关联的设备
    device = db.relationship('Device', backref='snap_space', uselist=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'space_name': self.space_name,
            'space_code': self.space_code,
            'bucket_name': self.bucket_name,
            'save_mode': self.save_mode,
            'save_time': self.save_time,
            'description': self.description,
            'device_id': self.device_id,
            'task_count': len(self.snap_tasks) if self.snap_tasks else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RecordSpace(db.Model):
    """监控录像空间表"""
    __tablename__ = 'record_space'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    space_name = db.Column(db.String(255), nullable=False, comment='空间名称')
    space_code = db.Column(db.String(255), nullable=False, unique=True, comment='空间编号（唯一标识）')
    bucket_name = db.Column(db.String(255), nullable=False, comment='MinIO bucket名称')
    save_mode = db.Column(db.SmallInteger, default=0, nullable=False, comment='文件保存模式[0:标准存储,1:归档存储]')
    save_time = db.Column(db.Integer, default=0, nullable=False, comment='文件保存时间[0:永久保存,>=7(单位:天)]')
    description = db.Column(db.String(500), nullable=True, comment='空间描述')
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='SET NULL'), nullable=True, unique=True, comment='关联的设备ID（一对一关系）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的设备
    device = db.relationship('Device', backref='record_space', uselist=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'space_name': self.space_name,
            'space_code': self.space_code,
            'bucket_name': self.bucket_name,
            'save_mode': self.save_mode,
            'save_time': self.save_time,
            'description': self.description,
            'device_id': self.device_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SnapTask(db.Model):
    """抓拍任务表"""
    __tablename__ = 'snap_task'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(255), nullable=False, comment='任务名称')
    task_code = db.Column(db.String(255), nullable=False, unique=True, comment='任务编号（唯一标识）')
    space_id = db.Column(db.Integer, db.ForeignKey('snap_space.id', ondelete='CASCADE'), nullable=False, comment='所属抓拍空间ID')
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='CASCADE'), nullable=False, comment='设备ID')
    
    # 抓拍配置
    capture_type = db.Column(db.SmallInteger, default=0, nullable=False, comment='抓拍类型[0:抽帧,1:抓拍]')
    cron_expression = db.Column(db.String(255), nullable=False, comment='Cron表达式')
    frame_skip = db.Column(db.Integer, default=1, nullable=False, comment='抽帧间隔（每N帧抓一次）')
    
    # 算法配置
    algorithm_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用算法推理')
    algorithm_type = db.Column(db.String(255), nullable=True, comment='算法类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]')
    algorithm_model_id = db.Column(db.Integer, nullable=True, comment='算法模型ID（关联AI模块的Model表）')
    algorithm_threshold = db.Column(db.Float, nullable=True, comment='算法阈值')
    algorithm_night_mode = db.Column(db.Boolean, default=False, nullable=False, comment='是否仅夜间(23点~8点)启用算法')
    
    # 告警配置
    alarm_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用告警')
    alarm_type = db.Column(db.SmallInteger, default=0, nullable=False, comment='告警类型[0:短信告警,1:邮箱告警,2:短信+邮箱]')
    phone_number = db.Column(db.String(500), nullable=True, comment='告警手机号[多个用英文逗号分割]')
    email = db.Column(db.String(500), nullable=True, comment='告警邮箱[多个用英文逗号分割]')
    # 新增告警通知配置
    notify_users = db.Column(db.Text, nullable=True, comment='通知人列表（JSON格式，包含用户ID、姓名、手机号、邮箱等）')
    notify_methods = db.Column(db.String(100), nullable=True, comment='通知方式[sms:短信,email:邮箱,app:应用内通知，多个用逗号分割]')
    alarm_suppress_time = db.Column(db.Integer, default=300, nullable=False, comment='告警通知抑制时间（秒），防止频繁通知，默认5分钟')
    last_notify_time = db.Column(db.DateTime, nullable=True, comment='最后通知时间')
    
    # 文件命名配置
    auto_filename = db.Column(db.Boolean, default=True, nullable=False, comment='是否自动命名[0:否,1:是]')
    custom_filename_prefix = db.Column(db.String(255), nullable=True, comment='自定义文件前缀')
    
    # 状态管理
    status = db.Column(db.SmallInteger, default=0, nullable=False, comment='状态[0:正常,1:异常]')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用[0:停用,1:启用]')
    exception_reason = db.Column(db.String(500), nullable=True, comment='异常原因')
    run_status = db.Column(db.String(20), default='stopped', nullable=False, comment='运行状态[running:运行中,stopped:已停止,restarting:重启中]')
    
    # 统计信息
    total_captures = db.Column(db.Integer, default=0, nullable=False, comment='总抓拍次数')
    last_capture_time = db.Column(db.DateTime, nullable=True, comment='最后抓拍时间')
    last_success_time = db.Column(db.DateTime, nullable=True, comment='最后成功时间')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的检测区域
    detection_regions = db.relationship('DetectionRegion', backref='snap_task', lazy=True, cascade='all, delete-orphan')
    # 关联的算法模型服务配置
    algorithm_services = db.relationship('AlgorithmModelService', backref='snap_task', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        import json
        notify_users_data = None
        if self.notify_users:
            try:
                notify_users_data = json.loads(self.notify_users)
            except:
                notify_users_data = self.notify_users
        
        services_list = [s.to_dict() for s in self.algorithm_services] if self.algorithm_services else []
        
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_code': self.task_code,
            'space_id': self.space_id,
            'space_name': self.snap_space.space_name if self.snap_space else None,
            'device_id': self.device_id,
            'device_name': None,  # 需要通过关联查询获取
            'capture_type': self.capture_type,
            'cron_expression': self.cron_expression,
            'frame_skip': self.frame_skip,
            'algorithm_enabled': self.algorithm_enabled,
            'algorithm_type': self.algorithm_type,
            'algorithm_model_id': self.algorithm_model_id,
            'algorithm_threshold': self.algorithm_threshold,
            'algorithm_night_mode': self.algorithm_night_mode,
            'alarm_enabled': self.alarm_enabled,
            'alarm_type': self.alarm_type,
            'phone_number': self.phone_number,
            'email': self.email,
            'notify_users': notify_users_data,
            'notify_methods': self.notify_methods,
            'alarm_suppress_time': self.alarm_suppress_time,
            'last_notify_time': self.last_notify_time.isoformat() if self.last_notify_time else None,
            'auto_filename': self.auto_filename,
            'custom_filename_prefix': self.custom_filename_prefix,
            'status': self.status,
            'is_enabled': self.is_enabled,
            'run_status': self.run_status,
            'exception_reason': self.exception_reason,
            'total_captures': self.total_captures,
            'last_capture_time': self.last_capture_time.isoformat() if self.last_capture_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
            'algorithm_services': services_list,  # 关联的算法模型服务列表
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DetectionRegion(db.Model):
    """检测区域表"""
    __tablename__ = 'detection_region'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('snap_task.id', ondelete='CASCADE'), nullable=False, comment='所属任务ID')
    region_name = db.Column(db.String(255), nullable=False, comment='区域名称')
    region_type = db.Column(db.String(50), default='polygon', nullable=False, comment='区域类型[polygon:多边形,rectangle:矩形]')
    points = db.Column(db.Text, nullable=False, comment='区域坐标点(JSON格式，归一化坐标0-1)')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='SET NULL'), nullable=True, comment='参考图片ID（用于绘制区域的基准图片）')
    
    # 算法绑定（保留旧字段以兼容，新版本使用关联表）
    algorithm_type = db.Column(db.String(255), nullable=True, comment='绑定的算法类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]')
    algorithm_model_id = db.Column(db.Integer, nullable=True, comment='绑定的算法模型ID')
    algorithm_threshold = db.Column(db.Float, nullable=True, comment='算法阈值')
    algorithm_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用该区域的算法')
    
    # 显示配置
    color = db.Column(db.String(20), default='#FF5252', nullable=False, comment='区域显示颜色')
    opacity = db.Column(db.Float, default=0.3, nullable=False, comment='区域透明度(0-1)')
    
    # 状态
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用该区域')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序顺序')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的区域模型服务配置
    region_services = db.relationship('RegionModelService', backref='detection_region', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        import json
        try:
            points_data = json.loads(self.points) if self.points else []
        except:
            points_data = []
        
        # 获取关联的模型服务列表
        services_list = [s.to_dict() for s in self.region_services] if self.region_services else []
            
        return {
            'id': self.id,
            'task_id': self.task_id,
            'region_name': self.region_name,
            'region_type': self.region_type,
            'points': points_data,
            'image_id': self.image_id,
            'image_path': self.image.path if self.image else None,
            'algorithm_type': self.algorithm_type,
            'algorithm_model_id': self.algorithm_model_id,
            'algorithm_threshold': self.algorithm_threshold,
            'algorithm_enabled': self.algorithm_enabled,
            'color': self.color,
            'opacity': self.opacity,
            'is_enabled': self.is_enabled,
            'sort_order': self.sort_order,
            'services': services_list,  # 关联的模型服务列表
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlgorithmModelService(db.Model):
    """算法模型服务配置表（任务级别）"""
    __tablename__ = 'algorithm_model_service'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('snap_task.id', ondelete='CASCADE'), nullable=False, comment='所属任务ID')
    service_name = db.Column(db.String(255), nullable=False, comment='服务名称')
    service_url = db.Column(db.String(500), nullable=False, comment='AI模型服务请求接口URL')
    service_type = db.Column(db.String(100), nullable=True, comment='服务类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]')
    model_id = db.Column(db.Integer, nullable=True, comment='关联的模型ID')
    threshold = db.Column(db.Float, nullable=True, comment='检测阈值')
    request_method = db.Column(db.String(10), default='POST', nullable=False, comment='请求方法[GET,POST]')
    request_headers = db.Column(db.Text, nullable=True, comment='请求头（JSON格式）')
    request_body_template = db.Column(db.Text, nullable=True, comment='请求体模板（JSON格式，支持变量替换）')
    timeout = db.Column(db.Integer, default=30, nullable=False, comment='请求超时时间（秒）')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序顺序')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        import json
        headers = None
        if self.request_headers:
            try:
                headers = json.loads(self.request_headers)
            except:
                headers = self.request_headers
        
        body_template = None
        if self.request_body_template:
            try:
                body_template = json.loads(self.request_body_template)
            except:
                body_template = self.request_body_template
        
        return {
            'id': self.id,
            'task_id': self.task_id,
            'service_name': self.service_name,
            'service_url': self.service_url,
            'service_type': self.service_type,
            'model_id': self.model_id,
            'threshold': self.threshold,
            'request_method': self.request_method,
            'request_headers': headers,
            'request_body_template': body_template,
            'timeout': self.timeout,
            'is_enabled': self.is_enabled,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RegionModelService(db.Model):
    """区域模型服务配置表（区域级别）"""
    __tablename__ = 'region_model_service'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    region_id = db.Column(db.Integer, db.ForeignKey('detection_region.id', ondelete='CASCADE'), nullable=False, comment='所属检测区域ID')
    service_name = db.Column(db.String(255), nullable=False, comment='服务名称')
    service_url = db.Column(db.String(500), nullable=False, comment='AI模型服务请求接口URL')
    service_type = db.Column(db.String(100), nullable=True, comment='服务类型[FIRE:火焰烟雾检测,CROWD:人群聚集计数,SMOKE:吸烟检测等]')
    model_id = db.Column(db.Integer, nullable=True, comment='关联的模型ID')
    threshold = db.Column(db.Float, nullable=True, comment='检测阈值')
    request_method = db.Column(db.String(10), default='POST', nullable=False, comment='请求方法[GET,POST]')
    request_headers = db.Column(db.Text, nullable=True, comment='请求头（JSON格式）')
    request_body_template = db.Column(db.Text, nullable=True, comment='请求体模板（JSON格式，支持变量替换）')
    timeout = db.Column(db.Integer, default=30, nullable=False, comment='请求超时时间（秒）')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序顺序')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        import json
        headers = None
        if self.request_headers:
            try:
                headers = json.loads(self.request_headers)
            except:
                headers = self.request_headers
        
        body_template = None
        if self.request_body_template:
            try:
                body_template = json.loads(self.request_body_template)
            except:
                body_template = self.request_body_template
        
        return {
            'id': self.id,
            'region_id': self.region_id,
            'service_name': self.service_name,
            'service_url': self.service_url,
            'service_type': self.service_type,
            'model_id': self.model_id,
            'threshold': self.threshold,
            'request_method': self.request_method,
            'request_headers': headers,
            'request_body_template': body_template,
            'timeout': self.timeout,
            'is_enabled': self.is_enabled,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DeviceStorageConfig(db.Model):
    """设备存储配置表"""
    __tablename__ = 'device_storage_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='CASCADE'), nullable=False, unique=True, comment='设备ID')
    # 抓拍图片存储配置
    snap_storage_bucket = db.Column(db.String(255), nullable=True, comment='抓拍图片存储bucket名称')
    snap_storage_max_size = db.Column(db.BigInteger, nullable=True, comment='抓拍图片存储最大空间（字节），0表示不限制')
    snap_storage_cleanup_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用抓拍图片自动清理')
    snap_storage_cleanup_threshold = db.Column(db.Float, default=0.8, nullable=False, comment='抓拍图片清理阈值（使用率超过此值触发清理）')
    snap_storage_cleanup_ratio = db.Column(db.Float, default=0.3, nullable=False, comment='抓拍图片清理比例（清理最老的30%）')
    # 录像存储配置
    video_storage_bucket = db.Column(db.String(255), nullable=True, comment='录像存储bucket名称')
    video_storage_max_size = db.Column(db.BigInteger, nullable=True, comment='录像存储最大空间（字节），0表示不限制')
    video_storage_cleanup_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用录像自动清理')
    video_storage_cleanup_threshold = db.Column(db.Float, default=0.8, nullable=False, comment='录像清理阈值（使用率超过此值触发清理）')
    video_storage_cleanup_ratio = db.Column(db.Float, default=0.3, nullable=False, comment='录像清理比例（清理最老的30%）')
    # 最后清理时间
    last_snap_cleanup_time = db.Column(db.DateTime, nullable=True, comment='最后抓拍图片清理时间')
    last_video_cleanup_time = db.Column(db.DateTime, nullable=True, comment='最后录像清理时间')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'snap_storage_bucket': self.snap_storage_bucket,
            'snap_storage_max_size': self.snap_storage_max_size,
            'snap_storage_cleanup_enabled': self.snap_storage_cleanup_enabled,
            'snap_storage_cleanup_threshold': self.snap_storage_cleanup_threshold,
            'snap_storage_cleanup_ratio': self.snap_storage_cleanup_ratio,
            'video_storage_bucket': self.video_storage_bucket,
            'video_storage_max_size': self.video_storage_max_size,
            'video_storage_cleanup_enabled': self.video_storage_cleanup_enabled,
            'video_storage_cleanup_threshold': self.video_storage_cleanup_threshold,
            'video_storage_cleanup_ratio': self.video_storage_cleanup_ratio,
            'last_snap_cleanup_time': self.last_snap_cleanup_time.isoformat() if self.last_snap_cleanup_time else None,
            'last_video_cleanup_time': self.last_video_cleanup_time.isoformat() if self.last_video_cleanup_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Playback(db.Model):
    """录像回放表"""
    __tablename__ = 'playback'
    
    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # 主键
    file_path = db.Column(db.String(200), nullable=False)  # 文件路径
    event_time = db.Column(db.DateTime(timezone=True), nullable=False)  # 录制发生时间
    device_id = db.Column(db.String(30), nullable=False)  # 设备id
    device_name = db.Column(db.String(30), nullable=False)  # 设备名称
    duration = db.Column(db.SmallInteger(), nullable=False)  # 时长/秒
    thumbnail_path = db.Column(db.String(200), nullable=True)  # 封面图路径
    file_size = db.Column(db.BigInteger(), nullable=True)  # 文件大小（字节）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'duration': self.duration,
            'thumbnail_path': self.thumbnail_path,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
