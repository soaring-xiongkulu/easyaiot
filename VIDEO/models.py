"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
from datetime import datetime, timezone, timedelta

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
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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
    auto_snap_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否开启自动抓拍[默认不开启]')
    directory_id = db.Column(db.Integer, db.ForeignKey('device_directory.id', ondelete='SET NULL'), nullable=True, comment='所属目录ID')
    cover_image_path = db.Column(db.String(500), nullable=True, comment='摄像头封面展示图路径')
    images = db.relationship('Image', backref='project', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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
    pusher_id = db.Column(db.Integer, db.ForeignKey('pusher.id', ondelete='SET NULL'), nullable=True, comment='关联的推送器ID')
    
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联的检测区域（不使用数据库外键约束，仅ORM关系）
    # 注意：DetectionRegion.task_id 没有外键约束，需要通过 primaryjoin 明确指定关系
    # 关联的推送器
    pusher = db.relationship('Pusher', backref='snap_tasks', lazy=True)
    # 注意：算法模型服务现在关联到AlgorithmTask，不再关联SnapTask
    # 如果需要为抓拍任务配置算法服务，请使用区域级别的算法服务（RegionModelService）
    
    def to_dict(self):
        """转换为字典"""
        import json
        notify_users_data = None
        if self.notify_users:
            try:
                notify_users_data = json.loads(self.notify_users)
            except:
                notify_users_data = self.notify_users
        
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
            'pusher_id': self.pusher_id,
            'pusher_name': self.pusher.pusher_name if self.pusher else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DetectionRegion(db.Model):
    """检测区域表"""
    __tablename__ = 'detection_region'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 注意：task_id现在可以关联到algorithm_task（统一后的算法任务表）
    # 为了兼容，暂时保留对snap_task的引用，但新数据应使用algorithm_task
    task_id = db.Column(db.Integer, nullable=False, comment='所属任务ID（关联到algorithm_task或snap_task）')
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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


class FrameExtractor(db.Model):
    """抽帧器配置表"""
    __tablename__ = 'frame_extractor'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    extractor_name = db.Column(db.String(255), nullable=False, comment='抽帧器名称')
    extractor_code = db.Column(db.String(255), nullable=False, unique=True, comment='抽帧器编号（唯一标识）')
    extractor_type = db.Column(db.String(50), default='interval', nullable=False, comment='抽帧类型[interval:按间隔,time:按时间]')
    interval = db.Column(db.Integer, default=1, nullable=False, comment='抽帧间隔（每N帧抽一次，或每N秒抽一次）')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    
    # 心跳相关字段
    status = db.Column(db.String(20), default='stopped', nullable=False, comment='运行状态[running:运行中,stopped:已停止,error:错误]')
    server_ip = db.Column(db.String(50), nullable=True, comment='部署的服务器IP')
    port = db.Column(db.Integer, nullable=True, comment='服务端口')
    process_id = db.Column(db.Integer, nullable=True, comment='进程ID')
    last_heartbeat = db.Column(db.DateTime, nullable=True, comment='最后上报时间')
    log_path = db.Column(db.String(500), nullable=True, comment='日志文件路径')
    task_id = db.Column(db.Integer, nullable=True, comment='关联的算法任务ID')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'extractor_name': self.extractor_name,
            'extractor_code': self.extractor_code,
            'extractor_type': self.extractor_type,
            'interval': self.interval,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'status': self.status,
            'server_ip': self.server_ip,
            'port': self.port,
            'process_id': self.process_id,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'log_path': self.log_path,
            'task_id': self.task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Sorter(db.Model):
    """排序器配置表"""
    __tablename__ = 'sorter'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sorter_name = db.Column(db.String(255), nullable=False, comment='排序器名称')
    sorter_code = db.Column(db.String(255), nullable=False, unique=True, comment='排序器编号（唯一标识）')
    sorter_type = db.Column(db.String(50), default='confidence', nullable=False, comment='排序类型[confidence:置信度,time:时间,score:分数]')
    sort_order = db.Column(db.String(10), default='desc', nullable=False, comment='排序顺序[asc:升序,desc:降序]')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    
    # 心跳相关字段
    status = db.Column(db.String(20), default='stopped', nullable=False, comment='运行状态[running:运行中,stopped:已停止,error:错误]')
    server_ip = db.Column(db.String(50), nullable=True, comment='部署的服务器IP')
    port = db.Column(db.Integer, nullable=True, comment='服务端口')
    process_id = db.Column(db.Integer, nullable=True, comment='进程ID')
    last_heartbeat = db.Column(db.DateTime, nullable=True, comment='最后上报时间')
    log_path = db.Column(db.String(500), nullable=True, comment='日志文件路径')
    task_id = db.Column(db.Integer, nullable=True, comment='关联的算法任务ID')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'sorter_name': self.sorter_name,
            'sorter_code': self.sorter_code,
            'sorter_type': self.sorter_type,
            'sort_order': self.sort_order,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'status': self.status,
            'server_ip': self.server_ip,
            'port': self.port,
            'process_id': self.process_id,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'log_path': self.log_path,
            'task_id': self.task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Pusher(db.Model):
    """推送器配置表"""
    __tablename__ = 'pusher'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pusher_name = db.Column(db.String(255), nullable=False, comment='推送器名称')
    pusher_code = db.Column(db.String(255), nullable=False, unique=True, comment='推送器编号（唯一标识）')
    
    # 推送视频流配置（仅实时算法任务使用）
    video_stream_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用推送视频流')
    video_stream_url = db.Column(db.String(500), nullable=True, comment='视频流推送地址（RTMP/RTSP等，单摄像头时使用）')
    # 多摄像头RTMP推送映射(JSON格式: {"device_id1": "rtmp://url1", "device_id2": "rtmp://url2"})
    device_rtmp_mapping = db.Column(db.Text, nullable=True, comment='多摄像头RTMP推送映射（JSON格式，device_id -> rtmp_url）')
    video_stream_format = db.Column(db.String(50), default='rtmp', nullable=False, comment='视频流格式[rtmp:RTMP,rtsp:RTSP,webrtc:WebRTC]')
    video_stream_quality = db.Column(db.String(50), default='high', nullable=False, comment='视频流质量[low:低,medium:中,high:高]')
    
    # 推送事件告警配置（实时算法任务和抓拍算法任务都使用）
    event_alert_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用推送事件告警')
    event_alert_url = db.Column(db.String(500), nullable=True, comment='事件告警推送地址（HTTP/WebSocket/Kafka等）')
    event_alert_method = db.Column(db.String(20), default='http', nullable=False, comment='事件告警推送方式[http:HTTP,websocket:WebSocket,kafka:Kafka]')
    event_alert_format = db.Column(db.String(50), default='json', nullable=False, comment='事件告警数据格式[json:JSON,xml:XML]')
    event_alert_headers = db.Column(db.Text, nullable=True, comment='事件告警请求头（JSON格式）')
    event_alert_template = db.Column(db.Text, nullable=True, comment='事件告警数据模板（JSON格式，支持变量替换）')
    
    description = db.Column(db.String(500), nullable=True, comment='描述')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    
    # 心跳相关字段
    status = db.Column(db.String(20), default='stopped', nullable=False, comment='运行状态[running:运行中,stopped:已停止,error:错误]')
    server_ip = db.Column(db.String(50), nullable=True, comment='部署的服务器IP')
    port = db.Column(db.Integer, nullable=True, comment='服务端口')
    process_id = db.Column(db.Integer, nullable=True, comment='进程ID')
    last_heartbeat = db.Column(db.DateTime, nullable=True, comment='最后上报时间')
    log_path = db.Column(db.String(500), nullable=True, comment='日志文件路径')
    task_id = db.Column(db.Integer, nullable=True, comment='关联的算法任务ID')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    def to_dict(self):
        """转换为字典"""
        import json
        headers = None
        if self.event_alert_headers:
            try:
                headers = json.loads(self.event_alert_headers)
            except:
                headers = self.event_alert_headers
        
        template = None
        if self.event_alert_template:
            try:
                template = json.loads(self.event_alert_template)
            except:
                template = self.event_alert_template
        
        # 解析多摄像头RTMP映射
        device_rtmp_mapping = None
        if self.device_rtmp_mapping:
            try:
                device_rtmp_mapping = json.loads(self.device_rtmp_mapping)
            except:
                device_rtmp_mapping = self.device_rtmp_mapping
        
        return {
            'id': self.id,
            'pusher_name': self.pusher_name,
            'pusher_code': self.pusher_code,
            'video_stream_enabled': self.video_stream_enabled,
            'video_stream_url': self.video_stream_url,
            'device_rtmp_mapping': device_rtmp_mapping,
            'video_stream_format': self.video_stream_format,
            'video_stream_quality': self.video_stream_quality,
            'event_alert_enabled': self.event_alert_enabled,
            'event_alert_url': self.event_alert_url,
            'event_alert_method': self.event_alert_method,
            'event_alert_format': self.event_alert_format,
            'event_alert_headers': headers,
            'event_alert_template': template,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'status': self.status,
            'server_ip': self.server_ip,
            'port': self.port,
            'process_id': self.process_id,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'log_path': self.log_path,
            'task_id': self.task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_rtmp_url_for_device(self, device_id: str) -> str:
        """
        获取指定摄像头的RTMP推送地址
        
        Args:
            device_id: 摄像头ID
        
        Returns:
            str: RTMP推送地址
        """
        import json
        # 优先使用多摄像头映射
        if self.device_rtmp_mapping:
            try:
                mapping = json.loads(self.device_rtmp_mapping)
                if isinstance(mapping, dict) and device_id in mapping:
                    return mapping[device_id]
            except:
                pass
        
        # 如果没有映射,使用默认的video_stream_url
        return self.video_stream_url or ''


# 算法任务和摄像头的多对多关联表
algorithm_task_device = db.Table(
    'algorithm_task_device',
    db.Column('task_id', db.Integer, db.ForeignKey('algorithm_task.id', ondelete='CASCADE'), primary_key=True, comment='算法任务ID'),
    db.Column('device_id', db.String(100), db.ForeignKey('device.id', ondelete='CASCADE'), primary_key=True, comment='摄像头ID'),
    db.Column('created_at', db.DateTime, default=lambda: datetime.utcnow(), comment='创建时间')
)

# 推流转发任务和摄像头的多对多关联表
stream_forward_task_device = db.Table(
    'stream_forward_task_device',
    db.Column('stream_forward_task_id', db.Integer, db.ForeignKey('stream_forward_task.id', ondelete='CASCADE'), primary_key=True, comment='推流转发任务ID'),
    db.Column('device_id', db.String(100), db.ForeignKey('device.id', ondelete='CASCADE'), primary_key=True, comment='摄像头ID'),
    db.Column('created_at', db.DateTime, default=lambda: datetime.utcnow(), comment='创建时间')
)


class AlgorithmTask(db.Model):
    """算法任务表（统一管理实时算法任务和抓拍算法任务）"""
    __tablename__ = 'algorithm_task'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(255), nullable=False, comment='任务名称')
    task_code = db.Column(db.String(255), nullable=False, unique=True, comment='任务编号（唯一标识）')
    
    # 任务类型：realtime=实时算法任务（分析RTSP/RTMP流），snap=抓拍算法任务（分析抽帧图片）
    task_type = db.Column(db.String(20), default='realtime', nullable=False, comment='任务类型[realtime:实时算法任务,snap:抓拍算法任务]')
    
    # 模型配置（直接选择模型列表，不再依赖模型服务接口）
    model_ids = db.Column(db.Text, nullable=True, comment='关联的模型ID列表（JSON格式，如[1,2,3]）')
    model_names = db.Column(db.Text, nullable=True, comment='关联的模型名称列表（逗号分隔，冗余字段，用于快速显示）')
    
    # 实时算法任务配置
    extract_interval = db.Column(db.Integer, default=25, nullable=False, comment='抽帧间隔（每N帧抽一次，仅实时算法任务）')
    rtmp_input_url = db.Column(db.String(500), nullable=True, comment='RTMP输入流地址（仅实时算法任务）')
    rtmp_output_url = db.Column(db.String(500), nullable=True, comment='RTMP输出流地址（仅实时算法任务）')
    
    # 追踪配置
    tracking_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用目标追踪')
    tracking_similarity_threshold = db.Column(db.Float, default=0.2, nullable=False, comment='追踪相似度阈值')
    tracking_max_age = db.Column(db.Integer, default=25, nullable=False, comment='追踪目标最大存活帧数')
    tracking_smooth_alpha = db.Column(db.Float, default=0.25, nullable=False, comment='追踪平滑系数')
    
    # 告警事件配置
    alert_event_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用告警事件')
    
    # 告警通知配置
    alert_notification_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用告警通知')
    alert_notification_config = db.Column(db.Text, nullable=True, comment='告警通知配置（JSON格式，包含通知渠道和模板配置，格式：{"channels": [{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]}）')
    alarm_suppress_time = db.Column(db.Integer, default=300, nullable=False, comment='告警通知抑制时间（秒），防止频繁通知，默认5分钟')
    last_notify_time = db.Column(db.DateTime, nullable=True, comment='最后通知时间')
    
    # 抓拍相关配置（仅抓拍算法任务使用）
    space_id = db.Column(db.Integer, db.ForeignKey('snap_space.id', ondelete='CASCADE'), nullable=True, comment='所属抓拍空间ID（仅抓拍算法任务）')
    cron_expression = db.Column(db.String(255), nullable=True, comment='Cron表达式（仅抓拍算法任务）')
    frame_skip = db.Column(db.Integer, default=1, nullable=False, comment='抽帧间隔（每N帧抓一次，仅抓拍算法任务）')
    
    # 状态管理
    status = db.Column(db.SmallInteger, default=0, nullable=False, comment='状态[0:正常,1:异常]')
    is_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用[0:停用,1:启用]')
    run_status = db.Column(db.String(20), default='stopped', nullable=False, comment='运行状态[running:运行中,stopped:已停止,restarting:重启中]')
    exception_reason = db.Column(db.String(500), nullable=True, comment='异常原因')
    
    # 服务状态信息（仅实时算法任务使用）
    service_server_ip = db.Column(db.String(45), nullable=True, comment='服务运行服务器IP')
    service_port = db.Column(db.Integer, nullable=True, comment='服务端口')
    service_process_id = db.Column(db.Integer, nullable=True, comment='服务进程ID')
    service_last_heartbeat = db.Column(db.DateTime, nullable=True, comment='服务最后心跳时间')
    service_log_path = db.Column(db.String(500), nullable=True, comment='服务日志路径')
    
    # 统计信息
    total_frames = db.Column(db.Integer, default=0, nullable=False, comment='总处理帧数')
    total_detections = db.Column(db.Integer, default=0, nullable=False, comment='总检测次数')
    total_captures = db.Column(db.Integer, default=0, nullable=False, comment='总抓拍次数（仅抓拍算法任务）')
    last_process_time = db.Column(db.DateTime, nullable=True, comment='最后处理时间')
    last_success_time = db.Column(db.DateTime, nullable=True, comment='最后成功时间')
    last_capture_time = db.Column(db.DateTime, nullable=True, comment='最后抓拍时间（仅抓拍算法任务）')
    
    description = db.Column(db.String(500), nullable=True, comment='任务描述')
    
    # 布防时段配置
    defense_mode = db.Column(db.String(20), default='half', nullable=False, comment='布防模式[full:全防模式,half:半防模式,day:白天模式,night:夜间模式]')
    defense_schedule = db.Column(db.Text, nullable=True, comment='布防时段配置（JSON格式，7天×24小时的二维数组）')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联关系
    devices = db.relationship('Device', secondary=algorithm_task_device, backref='algorithm_task_list', lazy=True)  # 多对多关系
    snap_space = db.relationship('SnapSpace', backref='algorithm_tasks', lazy=True)
    # 检测区域关联（通过task_id关联，支持统一后的算法任务，不使用数据库外键约束）
    # 注意：关系在文件末尾使用实际列对象配置
    
    def to_dict(self):
        """转换为字典"""
        import json
        
        # 解析模型ID列表
        model_ids_list = []
        if self.model_ids:
            try:
                model_ids_list = json.loads(self.model_ids) if isinstance(self.model_ids, str) else self.model_ids
            except:
                pass
        
        # 获取关联的摄像头列表
        device_list = self.devices if self.devices else []
        device_ids = [d.id for d in device_list]
        device_names = [d.name or d.id for d in device_list]
        
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_code': self.task_code,
            'task_type': self.task_type,
            'device_ids': device_ids,
            'device_names': device_names,
            'model_ids': model_ids_list,
            'model_names': self.model_names,
            'extract_interval': self.extract_interval,
            'rtmp_input_url': self.rtmp_input_url,
            'rtmp_output_url': self.rtmp_output_url,
            'tracking_enabled': self.tracking_enabled,
            'tracking_similarity_threshold': self.tracking_similarity_threshold,
            'tracking_max_age': self.tracking_max_age,
            'tracking_smooth_alpha': self.tracking_smooth_alpha,
            'alert_event_enabled': self.alert_event_enabled,
            'alert_notification_enabled': self.alert_notification_enabled,
            'alert_notification_config': json.loads(self.alert_notification_config) if self.alert_notification_config else None,
            'alarm_suppress_time': self.alarm_suppress_time,
            'last_notify_time': self.last_notify_time.isoformat() if self.last_notify_time else None,
            'space_id': self.space_id,
            'space_name': self.snap_space.space_name if self.snap_space else None,
            'cron_expression': self.cron_expression,
            'frame_skip': self.frame_skip,
            'status': self.status,
            'is_enabled': self.is_enabled,
            'exception_reason': self.exception_reason,
            'total_frames': self.total_frames,
            'total_detections': self.total_detections,
            'total_captures': self.total_captures,
            'last_process_time': self.last_process_time.isoformat() if self.last_process_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
            'last_capture_time': self.last_capture_time.isoformat() if self.last_capture_time else None,
            'defense_mode': self.defense_mode,
            'defense_schedule': self.defense_schedule,
            'service_server_ip': self.service_server_ip,
            'service_port': self.service_port,
            'service_process_id': self.service_process_id,
            'service_last_heartbeat': self.service_last_heartbeat.isoformat() if self.service_last_heartbeat else None,
            'service_log_path': self.service_log_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TrackingTarget(db.Model):
    """追踪目标记录表（记录对象出现、停留、离开时间等信息）"""
    __tablename__ = 'tracking_target'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('algorithm_task.id', ondelete='CASCADE'), nullable=False, comment='所属算法任务ID')
    device_id = db.Column(db.String(100), nullable=False, comment='设备ID')
    device_name = db.Column(db.String(255), nullable=True, comment='设备名称')
    track_id = db.Column(db.Integer, nullable=False, comment='追踪ID（同一任务内唯一）')
    class_id = db.Column(db.Integer, nullable=True, comment='类别ID')
    class_name = db.Column(db.String(100), nullable=True, comment='类别名称')
    first_seen_time = db.Column(db.DateTime, nullable=False, comment='首次出现时间')
    last_seen_time = db.Column(db.DateTime, nullable=True, comment='最后出现时间')
    leave_time = db.Column(db.DateTime, nullable=True, comment='离开时间')
    duration = db.Column(db.Float, nullable=True, comment='停留时长（秒）')
    first_seen_frame = db.Column(db.Integer, nullable=True, comment='首次出现帧号')
    last_seen_frame = db.Column(db.Integer, nullable=True, comment='最后出现帧号')
    total_detections = db.Column(db.Integer, default=0, nullable=False, comment='总检测次数')
    information = db.Column(db.Text, nullable=True, comment='详细信息（JSON格式）')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联关系
    algorithm_task = db.relationship('AlgorithmTask', backref='tracking_targets', lazy=True)
    
    def to_dict(self):
        """转换为字典"""
        import json
        information_dict = None
        if self.information:
            try:
                information_dict = json.loads(self.information) if isinstance(self.information, str) else self.information
            except:
                pass
        
        return {
            'id': self.id,
            'task_id': self.task_id,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'track_id': self.track_id,
            'class_id': self.class_id,
            'class_name': self.class_name,
            'first_seen_time': self.first_seen_time.isoformat() if self.first_seen_time else None,
            'last_seen_time': self.last_seen_time.isoformat() if self.last_seen_time else None,
            'leave_time': self.leave_time.isoformat() if self.leave_time else None,
            'duration': self.duration,
            'first_seen_frame': self.first_seen_frame,
            'last_seen_frame': self.last_seen_frame,
            'total_detections': self.total_detections,
            'information': information_dict,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlgorithmModelService(db.Model):
    """算法模型服务配置表（算法任务级别）"""
    __tablename__ = 'algorithm_model_service'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('algorithm_task.id', ondelete='CASCADE'), nullable=False, comment='所属算法任务ID')
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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


class DeviceDetectionRegion(db.Model):
    """设备检测区域表（独立于算法任务的区域检测配置）"""
    __tablename__ = 'device_detection_region'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='CASCADE'), nullable=False, comment='设备ID')
    region_name = db.Column(db.String(255), nullable=False, comment='区域名称')
    region_type = db.Column(db.String(50), default='polygon', nullable=False, comment='区域类型[polygon:多边形,line:线条]')
    points = db.Column(db.Text, nullable=False, comment='区域坐标点(JSON格式，归一化坐标0-1)')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='SET NULL'), nullable=True, comment='参考图片ID（用于绘制区域的基准图片）')
    
    # 显示配置
    color = db.Column(db.String(20), default='#FF5252', nullable=False, comment='区域显示颜色')
    opacity = db.Column(db.Float, default=0.3, nullable=False, comment='区域透明度(0-1)')
    
    # 状态
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用该区域')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序顺序')
    
    # 模型绑定
    model_ids = db.Column(db.Text, nullable=True, comment='关联的算法模型ID列表（JSON格式，如[1,2,3]）')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联关系
    device = db.relationship('Device', backref='detection_regions', lazy=True)
    image = db.relationship('Image', backref='device_detection_regions', lazy=True)
    
    def to_dict(self):
        """转换为字典"""
        import json
        try:
            points_data = json.loads(self.points) if self.points else []
        except:
            points_data = []
        
        # 解析 model_ids
        model_ids_list = []
        if self.model_ids:
            try:
                model_ids_list = json.loads(self.model_ids) if isinstance(self.model_ids, str) else self.model_ids
            except:
                model_ids_list = []
        
        return {
            'id': self.id,
            'device_id': self.device_id,
            'region_name': self.region_name,
            'region_type': self.region_type,
            'points': points_data,
            'image_id': self.image_id,
            'image_path': self.image.path if self.image else None,
            'color': self.color,
            'opacity': self.opacity,
            'is_enabled': self.is_enabled,
            'sort_order': self.sort_order,
            'model_ids': model_ids_list,
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
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
    # 使用带时区的本地时间（Asia/Shanghai，UTC+8）
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=8))))  # 创建时间
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=8))), onupdate=lambda: datetime.now(timezone(timedelta(hours=8))))  # 更新时间
    
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


# 在类定义之后配置关系，使用实际的列对象（不使用数据库外键约束）
# 配置 SnapTask 和 DetectionRegion 的关系
SnapTask.detection_regions = db.relationship(
    'DetectionRegion',
    primaryjoin='SnapTask.id == DetectionRegion.task_id',
    foreign_keys=[DetectionRegion.task_id],
    backref=db.backref('snap_task', lazy=True, overlaps="detection_regions,algorithm_task_ref"),
    lazy=True,
    cascade='all, delete-orphan',
    overlaps="detection_regions,algorithm_task_ref"
)

# 配置 AlgorithmTask 和 DetectionRegion 的关系
AlgorithmTask.detection_regions = db.relationship(
    'DetectionRegion',
    primaryjoin='AlgorithmTask.id == DetectionRegion.task_id',
    foreign_keys=[DetectionRegion.task_id],
    backref=db.backref('algorithm_task_ref', lazy=True, overlaps="detection_regions,snap_task"),
    lazy=True,
    cascade='all, delete-orphan',
    overlaps="detection_regions,snap_task"
)


class StreamForwardTask(db.Model):
    """推流转发任务表（用于批量推送多个摄像头实时画面，无需AI）"""
    __tablename__ = 'stream_forward_task'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(255), nullable=False, comment='任务名称')
    task_code = db.Column(db.String(255), nullable=False, unique=True, comment='任务编号（唯一标识）')
    
    # 推流配置
    output_format = db.Column(db.String(50), default='rtmp', nullable=False, comment='输出格式[rtmp:RTMP,rtsp:RTSP]')
    output_quality = db.Column(db.String(50), default='high', nullable=False, comment='输出质量[low:低,medium:中,high:高]')
    output_bitrate = db.Column(db.String(50), nullable=True, comment='输出码率（如512k,1M等，为空则使用默认值）')
    
    # 状态管理
    status = db.Column(db.SmallInteger, default=0, nullable=False, comment='状态[0:正常,1:异常]')
    is_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用[0:停用,1:启用]')
    exception_reason = db.Column(db.String(500), nullable=True, comment='异常原因')
    
    # 服务状态信息
    service_server_ip = db.Column(db.String(45), nullable=True, comment='服务运行服务器IP')
    service_port = db.Column(db.Integer, nullable=True, comment='服务端口')
    service_process_id = db.Column(db.Integer, nullable=True, comment='服务进程ID')
    service_last_heartbeat = db.Column(db.DateTime, nullable=True, comment='服务最后心跳时间')
    service_log_path = db.Column(db.String(500), nullable=True, comment='服务日志路径')
    
    # 统计信息
    total_streams = db.Column(db.Integer, default=0, nullable=False, comment='总推流数')
    last_process_time = db.Column(db.DateTime, nullable=True, comment='最后处理时间')
    last_success_time = db.Column(db.DateTime, nullable=True, comment='最后成功时间')
    
    description = db.Column(db.String(500), nullable=True, comment='任务描述')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联关系
    devices = db.relationship('Device', secondary=stream_forward_task_device, backref='stream_forward_task_list', lazy=True)  # 多对多关系
    
    def to_dict(self):
        """转换为字典"""
        # 获取关联的摄像头列表
        device_list = self.devices if self.devices else []
        device_ids = [d.id for d in device_list]
        device_names = [d.name or d.id for d in device_list]
        
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_code': self.task_code,
            'device_ids': device_ids,
            'device_names': device_names,
            'output_format': self.output_format,
            'output_quality': self.output_quality,
            'output_bitrate': self.output_bitrate,
            'status': self.status,
            'is_enabled': self.is_enabled,
            'exception_reason': self.exception_reason,
            'service_server_ip': self.service_server_ip,
            'service_port': self.service_port,
            'service_process_id': self.service_process_id,
            'service_last_heartbeat': self.service_last_heartbeat.isoformat() if self.service_last_heartbeat else None,
            'service_log_path': self.service_log_path,
            'total_streams': self.total_streams,
            'last_process_time': self.last_process_time.isoformat() if self.last_process_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
