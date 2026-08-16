"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
from datetime import datetime, timezone, timedelta

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


SHANGHAI_TZ = timezone(timedelta(hours=8))


def utc_isoformat_z(dt):
    """naive UTC（与 utcnow 一致）序列化为带 Z 的 ISO-8601，便于前端按 UTC 解析后再格式化为本地时间。"""
    if dt is None:
        return None
    u = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    return u.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def parse_shanghai_naive_to_utc_naive(dt):
    """将无时区 datetime 按 Asia/Shanghai 理解并转为数据库存储用的 UTC naive。"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(tzinfo=SHANGHAI_TZ).astimezone(timezone.utc).replace(tzinfo=None)


class DeviceDirectory(db.Model):
    """设备目录表，用于管理摄像头的目录结构"""
    __tablename__ = 'device_directory'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='目录名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('device_directory.id', ondelete='CASCADE'), nullable=True, comment='父目录ID，NULL表示根目录')
    description = db.Column(db.String(500), nullable=True, comment='目录描述')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序顺序')
    snap_save_time = db.Column(db.Integer, default=1, nullable=False, comment='抓拍保存时长[0:永久,>=1:小时]，目录内非自定义设备继承此值')
    record_save_time = db.Column(db.Integer, default=1, nullable=False, comment='录像保存时长[0:永久,>=1:小时]，目录内非自定义设备继承此值')
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
    ai_rtmp_stream = db.Column(db.Text, nullable=True, comment='AI推流地址（用于算法任务）')
    ai_http_stream = db.Column(db.Text, nullable=True, comment='AI HTTP地址（用于算法任务）')
    stream = db.Column(db.SmallInteger, nullable=True)
    ip = db.Column(db.String(45), nullable=True)
    port = db.Column(db.SMALLINT, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    skylink_token = db.Column(db.Text, nullable=True, comment='大疆司空 X-User-Token（机场/无人机共用）')
    mac = db.Column(db.String(17), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    firmware_version = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(300), nullable=True)
    hardware_id = db.Column(db.String(100), nullable=True)
    support_move = db.Column(db.Boolean, nullable=True)
    support_zoom = db.Column(db.Boolean, nullable=True)
    nvr_id = db.Column(db.Integer, db.ForeignKey('nvr.id', ondelete='SET NULL'), nullable=True)
    nvr_channel = db.Column(db.SmallInteger, nullable=False, default=0, comment='NVR 通道号，0 表示非 NVR 挂载')
    rtsp_direct = db.Column(db.Text, nullable=True, comment='摄像头直连 RTSP（经 NVR 枚举时 rtsp_direct）')
    channel_online = db.Column(db.Boolean, nullable=True, comment='NVR 通道在线状态')
    connection_status = db.Column(db.String(100), nullable=True, comment='NVR 通道连接状态/探测备注')
    nvr = db.relationship('Nvr', backref=db.backref('cameras', lazy=True), foreign_keys=[nvr_id])
    enable_forward = db.Column(db.Boolean, nullable=True)
    auto_snap_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否开启自动抓拍[默认不开启]')
    directory_id = db.Column(db.Integer, db.ForeignKey('device_directory.id', ondelete='SET NULL'), nullable=True, comment='所属目录ID')
    cover_image_path = db.Column(db.String(500), nullable=True, comment='摄像头封面展示图路径')
    longitude = db.Column(db.Float, nullable=True, comment='WGS84 经度，用于地图展示')
    latitude = db.Column(db.Float, nullable=True, comment='WGS84 纬度，用于地图展示')
    altitude = db.Column(db.Float, nullable=True, comment='海拔高度(米)，可选')
    address = db.Column(db.String(500), nullable=True, comment='安装地址或位置描述')
    location_source = db.Column(db.String(20), nullable=True, comment='位置来源: manual/gb28181/import')
    location_updated_at = db.Column(db.DateTime, nullable=True, comment='位置信息最后更新时间')
    heading = db.Column(db.Float, nullable=True, comment='安装朝向(度)，0=正北，顺时针')
    # GB28181 通道目录属性（由国标同步写入，供地图区分相机结构/朝向/业务分类）
    ptz_type = db.Column(db.SmallInteger, nullable=True, comment='摄像机结构: 1球机 2半球 3固定枪机 4遥控枪机 5遥控半球 6/7多目')
    direction_type = db.Column(db.SmallInteger, nullable=True, comment='监视方位(光轴): 1东2西3南4北5东南6东北7西南8西北')
    position_type = db.Column(db.SmallInteger, nullable=True, comment='位置类型: 1检查站2党政3车站码头4中心广场5体育场馆6商业中心7宗教8校园周边9治安复杂10交通干线')
    room_type = db.Column(db.SmallInteger, nullable=True, comment='安装位置: 1室外 2室内')
    use_type = db.Column(db.SmallInteger, nullable=True, comment='用途: 1治安 2交通 3重点')
    supply_light_type = db.Column(db.SmallInteger, nullable=True, comment='补光: 1无 2红外 3白光 4激光 9其他')
    resolution = db.Column(db.String(100), nullable=True, comment='支持的分辨率(可多值)')
    images = db.relationship('Image', backref='project', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


class DeviceTrackSession(db.Model):
    """摄像头轨迹段：一次连续移动/巡逻/上报周期，供轨迹回放列表与分段展示。"""
    __tablename__ = 'device_track_session'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.String(100),
        db.ForeignKey('device.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='摄像头 device.id',
    )
    title = db.Column(db.String(200), nullable=True, comment='轨迹段名称，如 2024-06-03 巡逻')
    started_at = db.Column(db.DateTime, nullable=False, comment='轨迹段起始时间（首点 recorded_at）')
    ended_at = db.Column(db.DateTime, nullable=True, comment='轨迹段结束时间（末点 recorded_at）')
    point_count = db.Column(db.Integer, nullable=False, default=0, comment='轨迹点数量（冗余，便于列表展示）')
    distance_m = db.Column(db.Float, nullable=True, comment='轨迹总里程(米)，可选缓存')
    source = db.Column(
        db.String(20),
        nullable=False,
        default='gb28181',
        comment='来源: gb28181/gps/import/system',
    )
    external_key = db.Column(
        db.String(200),
        nullable=True,
        unique=True,
        comment='外部同步幂等键，如 gb28181:{sip}:{channel}:{date}',
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    points = db.relationship(
        'DeviceTrackPoint',
        backref='session',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'title': self.title,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'point_count': self.point_count,
            'distance_m': self.distance_m,
            'source': self.source,
            'external_key': self.external_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DeviceTrackPoint(db.Model):
    """摄像头轨迹点：时序 GPS/位置采样，供地图轨迹回放。"""
    __tablename__ = 'device_track_point'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.String(100),
        db.ForeignKey('device.id', ondelete='CASCADE'),
        nullable=False,
        comment='摄像头 device.id',
    )
    session_id = db.Column(
        db.BigInteger,
        db.ForeignKey('device_track_session.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='所属轨迹段，可为空（散点）',
    )
    recorded_at = db.Column(db.DateTime, nullable=False, comment='GPS/位置上报时间')
    longitude = db.Column(db.Float, nullable=False, comment='WGS84 经度')
    latitude = db.Column(db.Float, nullable=False, comment='WGS84 纬度')
    altitude = db.Column(db.Float, nullable=True, comment='海拔(米)')
    speed = db.Column(db.Float, nullable=True, comment='速度(km/h)')
    direction = db.Column(db.Float, nullable=True, comment='方向角(0-360度，正北为0)')
    accuracy_m = db.Column(db.Float, nullable=True, comment='定位精度(米)')
    source = db.Column(
        db.String(20),
        nullable=False,
        default='gb28181',
        comment='来源: gb28181/gps/import/alert/manual',
    )
    report_source = db.Column(
        db.String(50),
        nullable=True,
        comment='上报类型，如 Mobile Position / GPS Alarm',
    )
    external_key = db.Column(
        db.String(200),
        nullable=True,
        unique=True,
        comment='外部同步幂等键，防重复写入',
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    __table_args__ = (
        db.Index('ix_device_track_point_device_recorded', 'device_id', 'recorded_at'),
        db.Index('ix_device_track_point_session_recorded', 'session_id', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'session_id': self.session_id,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'altitude': self.altitude,
            'speed': self.speed,
            'direction': self.direction,
            'accuracy_m': self.accuracy_m,
            'source': self.source,
            'report_source': self.report_source,
            'external_key': self.external_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

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
    __tablename__ = 'nvr'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip = db.Column(db.String(45), nullable=False, index=True)
    port = db.Column(db.SmallInteger, nullable=False, default=80)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    vendor = db.Column(db.String(32), nullable=True, comment='hikvision/dahua 等')
    serial_number = db.Column(db.String(300), nullable=True)
    firmware_version = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(100), nullable=True)
    mac = db.Column(db.String(17), nullable=True)
    scheme = db.Column(db.String(8), nullable=True, default='http', comment='http/https')
    rtsp_url = db.Column(db.Text, nullable=True, comment='NVR 预览/取流 RTSP（对齐 hiktools）')
    source = db.Column(db.String(32), nullable=True, comment='探测来源 isapi/dahua_cgi 等')
    rtsp_template = db.Column(db.Text, nullable=True, comment='自定义 RTSP 路径模板')
    rtsp_port = db.Column(db.SmallInteger, nullable=True, comment='RTSP 端口，默认 554')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    @property
    def web_url(self) -> str:
        sch = self.scheme or ('https' if (self.port or 80) in (443, 8443) else 'http')
        return f'{sch}://{self.ip}:{self.port or 80}'

class Alert(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    object = db.Column(db.String(30), nullable=False)
    event = db.Column(db.String(30), nullable=False)
    region = db.Column(db.String(30), nullable=True)
    information = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text('NOW()'), index=True)
    # 与 device.id 一致（GB28181 等设备 ID 可达约 50 字符）
    device_id = db.Column(db.String(100), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)
    # GB28181 device_id 较长时绝对路径易超 200 字符导致截断，iot-sink 无法读盘上传 MinIO
    image_path = db.Column(db.String(500), nullable=True, comment='本地图片路径（算法落盘）')
    image_url = db.Column(db.String(500), nullable=True, comment='MinIO 下载路径（/api/v1/buckets/.../objects/download?prefix=...）')
    record_path = db.Column(db.String(500), nullable=True, comment='告警录像 MinIO 下载路径（/api/v1/buckets/.../objects/download?prefix=...），非宿主机 /data/playbacks 路径')
    task_type = db.Column(db.String(20), nullable=True, comment='告警事件类型[realtime:实时算法任务,snap:抓拍算法任务]')
    task_id = db.Column(db.Integer, nullable=True, comment='关联的任务ID')
    task_name = db.Column(db.String(255), nullable=True, comment='关联的任务名称')
    # 通知人信息字段（用于追溯）
    notify_users = db.Column(db.Text, nullable=True, comment='通知人列表（JSON格式，格式：[{"phone": "xxx", "email": "xxx", "name": "xxx"}, ...]）')
    channels = db.Column(db.Text, nullable=True, comment='通知渠道配置（JSON格式，格式：[{"method": "sms", "template_id": "xxx"}, ...]）')
    notification_sent = db.Column(db.Boolean, default=False, nullable=False, comment='是否已发送通知')
    notification_sent_time = db.Column(db.DateTime, nullable=True, comment='通知发送时间')
    business_tags = db.Column(db.Text, nullable=True, comment='业务标签（JSON数组，库匹配告警携带匹配库标签）')
    correlation_id = db.Column(db.String(36), nullable=True, index=True, comment='关联事件ID（同一帧算法告警/人脸/车牌）')
    # 边缘节点维度（区分多 EDGE 集群数据）
    edge_node_id = db.Column(db.BigInteger, nullable=True, index=True, comment='边缘节点 edge_node.id')
    edge_node_name = db.Column(db.String(128), nullable=True, comment='边缘节点名称（冗余）')
    edge_node_host = db.Column(db.String(128), nullable=True, comment='边缘节点主机（冗余）')
    node_id = db.Column(db.BigInteger, nullable=True, comment='运行 compute_node.id（可选）')


class SnapSpace(db.Model):
    """抓拍空间表"""
    __tablename__ = 'snap_space'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    space_name = db.Column(db.String(255), nullable=False, comment='空间名称')
    space_code = db.Column(db.String(255), nullable=False, unique=True, comment='空间编号（唯一标识）')
    bucket_name = db.Column(db.String(255), nullable=False, comment='MinIO bucket名称')
    save_mode = db.Column(db.SmallInteger, default=0, nullable=False, comment='文件保存模式[0:标准存储,1:归档存储]')
    save_time = db.Column(db.Integer, default=1, nullable=False, comment='文件保存时长[0:永久保存,>=1(单位:小时)]')
    save_time_custom = db.Column(db.Boolean, default=False, nullable=False, comment='是否自定义保存时间（False 时跟随目录默认值）')
    description = db.Column(db.String(500), nullable=True, comment='空间描述')
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='SET NULL'), nullable=True, unique=True, comment='关联的设备ID（一对一关系）')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联的抓拍任务
    snap_tasks = db.relationship('SnapTask', backref='snap_space', lazy=True, cascade='all, delete-orphan')
    # 关联的设备
    device = db.relationship('Device', backref='snap_space', uselist=False)
    snap_images = db.relationship('SnapImage', backref='snap_space', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        from app.services.space_save_time_service import enrich_snap_space_dict
        return enrich_snap_space_dict({
            'id': self.id,
            'space_name': self.space_name,
            'space_code': self.space_code,
            'bucket_name': self.bucket_name,
            'save_mode': self.save_mode,
            'save_time': self.save_time,
            'save_time_custom': self.save_time_custom,
            'description': self.description,
            'device_id': self.device_id,
            'task_count': len(self.snap_tasks) if self.snap_tasks else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }, self)


class RecordSpace(db.Model):
    """监控录像空间表"""
    __tablename__ = 'record_space'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    space_name = db.Column(db.String(255), nullable=False, comment='空间名称')
    space_code = db.Column(db.String(255), nullable=False, unique=True, comment='空间编号（唯一标识）')
    bucket_name = db.Column(db.String(255), nullable=False, comment='MinIO bucket名称')
    save_mode = db.Column(db.SmallInteger, default=0, nullable=False, comment='文件保存模式[0:标准存储,1:归档存储]')
    save_time = db.Column(db.Integer, default=1, nullable=False, comment='文件保存时长[0:永久保存,>=1(单位:小时)]')
    save_time_custom = db.Column(db.Boolean, default=False, nullable=False, comment='是否自定义保存时间（False 时跟随目录默认值）')
    description = db.Column(db.String(500), nullable=True, comment='空间描述')
    device_id = db.Column(db.String(100), db.ForeignKey('device.id', ondelete='SET NULL'), nullable=True, unique=True, comment='关联的设备ID（一对一关系）')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联的设备
    device = db.relationship('Device', backref='record_space', uselist=False)
    record_files = db.relationship('RecordFile', backref='record_space', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        from app.services.space_save_time_service import enrich_record_space_dict
        return enrich_record_space_dict({
            'id': self.id,
            'space_name': self.space_name,
            'space_code': self.space_code,
            'bucket_name': self.bucket_name,
            'save_mode': self.save_mode,
            'save_time': self.save_time,
            'save_time_custom': self.save_time_custom,
            'description': self.description,
            'device_id': self.device_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }, self)


class SpaceGroupSavePolicy(db.Model):
    """NVR / GB28181 分组默认存储策略（联动更新组内非自定义设备空间）"""
    __tablename__ = 'space_group_save_policy'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_type = db.Column(db.String(20), nullable=False, comment='分组类型: nvr / gb28181')
    group_key = db.Column(db.String(100), nullable=False, comment='NVR ID 或国标 SIP 设备 ID')
    snap_save_time = db.Column(db.Integer, default=1, nullable=False, comment='抓拍保存时长[0:永久,>=1:小时]')
    record_save_time = db.Column(db.Integer, default=1, nullable=False, comment='录像保存时长[0:永久,>=1:小时]')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        db.UniqueConstraint('group_type', 'group_key', name='uq_space_group_save_policy'),
    )


class RecordFile(db.Model):
    """录像空间文件元数据表（MinIO 实体 + DB 索引，列表查询走数据库分页）"""
    __tablename__ = 'record_file'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    space_id = db.Column(db.Integer, db.ForeignKey('record_space.id', ondelete='CASCADE'), nullable=False, index=True)
    device_id = db.Column(db.String(100), nullable=False, index=True, comment='设备ID')
    object_name = db.Column(db.String(500), nullable=False, comment='MinIO 对象路径')
    bucket_name = db.Column(db.String(255), nullable=False, comment='MinIO bucket')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    file_size = db.Column(db.BigInteger, nullable=True, comment='文件大小（字节）')
    content_type = db.Column(db.String(100), default='video/mp4', comment='MIME 类型')
    etag = db.Column(db.String(128), nullable=True, comment='MinIO ETag')
    url = db.Column(db.String(500), nullable=False, comment='MinIO 下载地址')
    thumbnail_url = db.Column(db.String(500), nullable=True, comment='封面下载地址')
    duration = db.Column(db.SmallInteger, nullable=True, comment='时长（秒）')
    event_time = db.Column(db.DateTime, nullable=False, index=True, comment='录像时间（排序字段）')
    source = db.Column(db.String(50), default='dvr', nullable=False, comment='来源[dvr|manual]')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        db.UniqueConstraint('bucket_name', 'object_name', name='uq_record_file_bucket_object'),
        db.Index('ix_record_file_space_event_time', 'space_id', 'event_time'),
    )

    def to_list_item(self):
        from app.utils.service_urls import (
            is_local_filesystem_path,
            minio_storage_enabled,
            build_record_video_api_url,
        )
        display_url = self.url
        if not minio_storage_enabled() and is_local_filesystem_path(display_url or ''):
            display_url = build_record_video_api_url(self.space_id, self.object_name)
        elif not minio_storage_enabled() and not (display_url or '').startswith(('/api/', '/video/')):
            display_url = build_record_video_api_url(self.space_id, self.object_name)
        return {
            'id': self.id,
            'object_name': self.object_name,
            'filename': self.filename,
            'size': self.file_size or 0,
            'last_modified': self.event_time.isoformat() if self.event_time else None,
            'etag': self.etag or '',
            'content_type': self.content_type or 'video/mp4',
            'url': display_url,
            'duration': self.duration,
            'thumbnail_url': self.thumbnail_url,
        }


class SnapImage(db.Model):
    """抓拍空间图片元数据表（MinIO 实体 + DB 索引，列表查询走数据库分页）"""
    __tablename__ = 'snap_image'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    space_id = db.Column(db.Integer, db.ForeignKey('snap_space.id', ondelete='CASCADE'), nullable=False, index=True)
    device_id = db.Column(db.String(100), nullable=False, index=True, comment='设备ID')
    object_name = db.Column(db.String(500), nullable=False, comment='MinIO 对象路径')
    bucket_name = db.Column(db.String(255), nullable=False, comment='MinIO bucket')
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    file_size = db.Column(db.BigInteger, nullable=True, comment='文件大小（字节）')
    content_type = db.Column(db.String(100), default='image/jpeg', comment='MIME 类型')
    etag = db.Column(db.String(128), nullable=True, comment='MinIO ETag')
    url = db.Column(db.String(500), nullable=False, comment='MinIO 下载地址')
    captured_at = db.Column(db.DateTime, nullable=False, index=True, comment='抓拍时间（排序字段）')
    task_id = db.Column(db.Integer, nullable=True, comment='关联抓拍任务ID')
    source = db.Column(db.String(50), default='snap', nullable=False, comment='来源[snap|frame|algorithm]')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    __table_args__ = (
        db.UniqueConstraint('bucket_name', 'object_name', name='uq_snap_image_bucket_object'),
        db.Index('ix_snap_image_space_captured_at', 'space_id', 'captured_at'),
    )

    def to_list_item(self):
        from app.utils.service_urls import (
            is_local_filesystem_path,
            minio_storage_enabled,
            build_snap_image_api_url,
        )
        display_url = self.url
        if minio_storage_enabled():
            pass
        elif is_local_filesystem_path(display_url or ''):
            display_url = build_snap_image_api_url(self.space_id, self.object_name)
        elif (display_url or '').startswith('/video/'):
            pass
        elif not (display_url or '').startswith('/api/'):
            display_url = build_snap_image_api_url(self.space_id, self.object_name)
        from app.utils.service_urls import shanghai_isoformat

        return {
            'id': self.id,
            'object_name': self.object_name,
            'filename': self.filename,
            'size': self.file_size or 0,
            'last_modified': shanghai_isoformat(self.captured_at),
            'captured_at': shanghai_isoformat(self.captured_at),
            'source': self.source or 'snap',
            'task_id': self.task_id,
            'etag': self.etag or '',
            'content_type': self.content_type or 'image/jpeg',
            'url': display_url,
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
            'last_heartbeat': utc_isoformat_z(self.last_heartbeat),
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
            'last_heartbeat': utc_isoformat_z(self.last_heartbeat),
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
            'last_heartbeat': utc_isoformat_z(self.last_heartbeat),
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
    
    # 任务类型：realtime=实时算法任务，snap=抓拍算法任务，patrol=巡检算法任务
    task_type = db.Column(db.String(20), default='realtime', nullable=False, comment='任务类型[realtime,snap,patrol]')
    
    # 模型配置（直接选择模型列表，不再依赖模型服务接口）
    model_ids = db.Column(db.Text, nullable=True, comment='关联的模型ID列表（JSON格式，如[1,2,3]）')
    model_names = db.Column(db.Text, nullable=True, comment='关联的模型名称列表（逗号分隔，冗余字段，用于快速显示）')
    detect_conf = db.Column(db.Float, default=0.5, nullable=False, comment='YOLO检测置信度阈值（0~1，默认0.5）')
    
    # 实时算法任务配置
    extract_interval = db.Column(db.Integer, default=12, nullable=True,
                                 comment='AI检测间隔（每N帧推理一次；12≈25fps下每秒2次；NULL时沿用EXTRACT_INTERVAL，默认12）')
    rtmp_input_url = db.Column(db.String(500), nullable=True, comment='RTMP输入流地址（仅实时算法任务）')
    rtmp_output_url = db.Column(db.String(500), nullable=True, comment='RTMP输出流地址（仅实时算法任务）')
    
    # 追踪配置
    tracking_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用目标追踪')
    tracking_similarity_threshold = db.Column(db.Float, default=0.2, nullable=False, comment='追踪相似度阈值')
    tracking_max_age = db.Column(db.Integer, default=25, nullable=False, comment='追踪目标最大存活帧数')
    tracking_smooth_alpha = db.Column(db.Float, default=0.25, nullable=False, comment='追踪平滑系数')
    
    # 告警事件配置
    alert_event_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用告警事件')
    alert_event_suppress_time = db.Column(db.Integer, default=5, nullable=False, comment='告警事件抑制时间（秒），同一设备两次上报告警事件的最小间隔，减轻Kafka积压，默认5秒')
    alert_class_names = db.Column(db.Text, nullable=True, comment='告警触发类别标签（JSON数组，为空则任意检测均可触发告警）')
    face_detection_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用人脸检测')
    plate_detection_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用车牌检测')
    face_matching_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用人脸匹配（默认关闭）')
    face_library_ids = db.Column(db.Text, nullable=True, comment='关联人脸库ID列表（JSON数组，多库匹配）')
    face_matching_threshold = db.Column(db.Float, nullable=True, comment='人脸匹配相似度阈值（为空则使用人脸库默认值）')
    plate_matching_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用车牌匹配（默认关闭）')
    plate_library_ids = db.Column(db.Text, nullable=True, comment='关联车牌库ID列表（JSON数组，多库匹配）')
    matching_business_tags = db.Column(db.Text, nullable=True, comment='匹配业务标签（JSON数组，透传子任务/告警）')
    
    # 告警通知配置
    alert_notification_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用告警通知')
    alert_notification_config = db.Column(db.Text, nullable=True, comment='告警通知配置（JSON格式，包含通知渠道和模板配置，格式：{"channels": [{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]}）')
    alarm_suppress_time = db.Column(db.Integer, default=300, nullable=False, comment='告警通知抑制时间（秒），防止频繁通知，默认5分钟')
    last_notify_time = db.Column(db.DateTime, nullable=True, comment='最后通知时间')
    
    # 抓拍相关配置（仅抓拍算法任务使用）
    space_id = db.Column(db.Integer, db.ForeignKey('snap_space.id', ondelete='CASCADE'), nullable=True, comment='所属抓拍空间ID（仅抓拍算法任务）')
    cron_expression = db.Column(db.String(255), nullable=True, comment='Cron表达式（仅抓拍算法任务）')
    frame_skip = db.Column(db.Integer, default=1, nullable=False, comment='抽帧间隔（每N帧抓一次，仅抓拍算法任务）')

    # 巡检算法任务配置（仅 patrol 类型）
    patrol_mode = db.Column(db.String(20), default='pool', nullable=True,
                            comment='巡检模式[rotate,pool,hybrid]')
    patrol_interval_sec = db.Column(db.Integer, default=10, nullable=True, comment='巡检间隔（秒）')
    patrol_pool_size = db.Column(db.Integer, default=4, nullable=True, comment='连接池大小')
    focus_device_id = db.Column(db.String(100), nullable=True, comment='焦点设备ID（hybrid）')
    
    # 状态管理
    status = db.Column(db.SmallInteger, default=0, nullable=False, comment='状态[0:正常,1:异常]')
    is_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用[0:停用,1:启用]')
    run_status = db.Column(db.String(20), default='stopped', nullable=False, comment='运行状态[running:运行中,stopped:已停止,restarting:重启中]')
    exception_reason = db.Column(db.String(500), nullable=True, comment='异常原因')
    
    # 节点调度（跨节点部署）
    schedule_policy = db.Column(db.String(20), default='local', nullable=False,
                                comment='调度策略[local:本机,auto:自动节点,node:指定节点]')
    prefer_gpu = db.Column(db.Boolean, default=True, nullable=False,
                           comment='自动调度时是否优先 GPU 节点')
    target_node_id = db.Column(db.BigInteger, nullable=True, comment='指定部署节点ID')
    node_id = db.Column(db.BigInteger, nullable=True, comment='实际运行节点ID')
    device_deployments = db.Column(
        db.Text,
        nullable=True,
        comment='设备级远程/分片部署明细 JSON：[{device_ids,node_id,host,workload_id,pid,local}]',
    )

    # 执行后端：python=现有 run_deploy；cpp=RUNTIME 二进制（realtime/snap/patrol，本机）
    executor = db.Column(db.String(20), default='cpp', nullable=False,
                         comment='执行后端[python,cpp]，默认 cpp')
    runtime_bin_path = db.Column(db.String(500), nullable=True,
                                 comment='RUNTIME 二进制路径（空则用 RUNTIME_BIN 或仓库默认）')
    runtime_control_port = db.Column(db.Integer, nullable=True,
                                     comment='RUNTIME HTTP 控制端口（8000-9000）')

    # 服务状态信息（仅实时算法任务使用）
    service_server_ip = db.Column(db.String(512), nullable=True, comment='服务运行服务器IP（多节点时为逗号分隔）')
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

    # SAM 补充识别配置
    sam_supplement_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用 SAM 补充识别')
    sam_supplement_config = db.Column(db.Text, nullable=True, comment='SAM 补充配置 JSON')

    # 运动检测门控（实时算法任务资源优化）
    motion_gate_enabled = db.Column(db.Boolean, default=False, nullable=False,
                                    comment='是否启用运动检测门控（仅实时算法任务）')
    motion_gate_config = db.Column(db.Text, nullable=True, comment='运动门控配置 JSON')

    # 人体姿态分析（YOLO Pose，参照 AI 模块）
    pose_analysis_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用人体姿态分析')
    pose_analysis_config = db.Column(db.Text, nullable=True, comment='人体姿态分析配置 JSON')

    # 姿态意图分析（场景姿态库匹配告警）
    pose_intent_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用姿态意图分析告警')
    pose_library_ids = db.Column(db.Text, nullable=True, comment='关联场景姿态库ID列表（JSON数组）')
    pose_intent_threshold = db.Column(db.Float, nullable=True, comment='姿态意图匹配阈值（为空则使用库默认值）')
    pose_intent_config = db.Column(db.Text, nullable=True, comment='姿态意图分析配置 JSON')

    # AI 后处理（用户 Python 脚本）
    post_process_enabled = db.Column(db.Boolean, default=False, nullable=False, comment='是否启用 AI 后处理脚本')
    post_process_script = db.Column(db.String(255), nullable=True, comment='后处理脚本文件名，默认 post_process.py')
    post_process_replicas = db.Column(db.Integer, default=1, nullable=False, comment='后处理 Worker 副本数（集群水平扩展）')
    
    # 布防时段配置
    defense_mode = db.Column(db.String(20), default='half', nullable=False, comment='布防模式[full:全防模式,half:半防模式,day:白天模式,night:夜间模式]')
    defense_schedule = db.Column(db.Text, nullable=True, comment='布防时段配置（JSON格式，7天×24小时的二维数组）')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联关系
    devices = db.relationship('Device', secondary=algorithm_task_device, backref='algorithm_task_list', lazy=True)  # 多对多关系
    snap_space = db.relationship('SnapSpace', backref='algorithm_tasks', lazy=True)
    # 算法模型服务关联（通过task_id关联）
    algorithm_services = db.relationship('AlgorithmModelService', backref='algorithm_task', lazy=True, cascade='all, delete-orphan')
    # 检测区域关联（通过task_id关联，支持统一后的算法任务，不使用数据库外键约束）
    # 注意：关系在文件末尾使用实际列对象配置
    
    def _parse_matching_business_tags(self):
        import json
        if not self.matching_business_tags:
            return []
        try:
            tags = json.loads(self.matching_business_tags) if isinstance(self.matching_business_tags, str) else self.matching_business_tags
            return tags if isinstance(tags, list) else []
        except Exception:
            return []

    def _parse_alert_class_names(self):
        from app.utils.alert_class_filter import parse_alert_class_names
        return parse_alert_class_names(self.alert_class_names)

    def _parse_device_deployments(self):
        import json
        raw = getattr(self, 'device_deployments', None)
        if not raw:
            return []
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def _parse_library_ids(raw) -> list:
        import json
        if not raw:
            return []
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, list):
                return [int(x) for x in parsed if x is not None and str(x).strip() != '']
        except Exception:
            pass
        return []

    @staticmethod
    def _resolve_library_names(library_ids, library_model):
        if not library_ids:
            return []
        names = []
        for lib_id in library_ids:
            lib = library_model.query.get(lib_id)
            if lib:
                names.append(lib.name)
        return names

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
        
        # 获取关联的算法模型服务列表
        algorithm_services_list = []
        if self.algorithm_services:
            algorithm_services_list = [s.to_dict() for s in self.algorithm_services]
        
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_code': self.task_code,
            'task_type': self.task_type,
            'device_ids': device_ids,
            'device_names': device_names,
            'model_ids': model_ids_list,
            'model_names': self.model_names,
            'detect_conf': self.detect_conf if self.detect_conf is not None else 0.5,
            'extract_interval': self.extract_interval,
            'rtmp_input_url': self.rtmp_input_url,
            'rtmp_output_url': self.rtmp_output_url,
            'tracking_enabled': self.tracking_enabled,
            'tracking_similarity_threshold': self.tracking_similarity_threshold,
            'tracking_max_age': self.tracking_max_age,
            'tracking_smooth_alpha': self.tracking_smooth_alpha,
            'alert_event_enabled': self.alert_event_enabled,
            'alert_event_suppress_time': self.alert_event_suppress_time,
            'alert_class_names': self._parse_alert_class_names(),
            'face_detection_enabled': self.face_detection_enabled,
            'plate_detection_enabled': self.plate_detection_enabled,
            'face_matching_enabled': self.face_matching_enabled,
            'face_library_ids': self._parse_library_ids(self.face_library_ids),
            'face_library_names': self._resolve_library_names(
                self._parse_library_ids(self.face_library_ids),
                FaceLibrary,
            ),
            'face_matching_threshold': self.face_matching_threshold,
            'plate_matching_enabled': self.plate_matching_enabled,
            'plate_library_ids': self._parse_library_ids(self.plate_library_ids),
            'plate_library_names': self._resolve_library_names(
                self._parse_library_ids(self.plate_library_ids),
                PlateLibrary,
            ),
            'matching_business_tags': self._parse_matching_business_tags(),
            'alert_notification_enabled': self.alert_notification_enabled,
            'alert_notification_config': json.loads(self.alert_notification_config) if self.alert_notification_config else None,
            'alarm_suppress_time': self.alarm_suppress_time,
            'last_notify_time': utc_isoformat_z(self.last_notify_time),
            'space_id': self.space_id,
            'space_name': self.snap_space.space_name if self.snap_space else None,
            'cron_expression': self.cron_expression,
            'frame_skip': self.frame_skip,
            'patrol_mode': self.patrol_mode,
            'patrol_interval_sec': self.patrol_interval_sec,
            'patrol_pool_size': self.patrol_pool_size,
            'focus_device_id': self.focus_device_id,
            'status': self.status,
            'is_enabled': self.is_enabled,
            'exception_reason': self.exception_reason,
            'total_frames': self.total_frames,
            'total_detections': self.total_detections,
            'total_captures': self.total_captures,
            'last_process_time': utc_isoformat_z(self.last_process_time),
            'last_success_time': utc_isoformat_z(self.last_success_time),
            'last_capture_time': utc_isoformat_z(self.last_capture_time),
            'defense_mode': self.defense_mode,
            'defense_schedule': self.defense_schedule,
            'schedule_policy': self.schedule_policy,
            'prefer_gpu': self.prefer_gpu if self.prefer_gpu is not None else True,
            'target_node_id': self.target_node_id,
            'node_id': self.node_id,
            'device_deployments': self._parse_device_deployments(),
            'executor': getattr(self, 'executor', None) or 'cpp',
            'runtime_bin_path': getattr(self, 'runtime_bin_path', None),
            'runtime_control_port': getattr(self, 'runtime_control_port', None),
            'service_server_ip': self.service_server_ip,
            'service_port': self.service_port,
            'service_process_id': self.service_process_id,
            'service_last_heartbeat': utc_isoformat_z(self.service_last_heartbeat),
            'service_log_path': self.service_log_path,
            'algorithm_services': algorithm_services_list,  # 添加算法模型服务列表
            'sam_supplement_enabled': bool(self.sam_supplement_enabled),
            'sam_supplement_config': json.loads(self.sam_supplement_config) if self.sam_supplement_config else None,
            'motion_gate_enabled': bool(getattr(self, 'motion_gate_enabled', False)),
            'motion_gate_config': json.loads(self.motion_gate_config) if getattr(self, 'motion_gate_config', None) else None,
            'pose_analysis_enabled': bool(getattr(self, 'pose_analysis_enabled', False)),
            'pose_analysis_config': json.loads(self.pose_analysis_config) if getattr(self, 'pose_analysis_config', None) else None,
            'pose_intent_enabled': bool(getattr(self, 'pose_intent_enabled', False)),
            'pose_library_ids': self._parse_library_ids(getattr(self, 'pose_library_ids', None)),
            'pose_library_names': self._resolve_library_names(
                self._parse_library_ids(getattr(self, 'pose_library_ids', None)),
                ScenarioPoseLibrary,
            ),
            'pose_intent_threshold': getattr(self, 'pose_intent_threshold', None),
            'pose_intent_config': json.loads(self.pose_intent_config) if getattr(self, 'pose_intent_config', None) else None,
            'post_process_enabled': bool(self.post_process_enabled),
            'post_process_script': self.post_process_script,
            'post_process_replicas': int(self.post_process_replicas or 1),
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at)
        }


class AlgorithmPostProcessResult(db.Model):
    """算法任务 AI 后处理结果（由 iot-sink Kafka 消费者异步写入）"""
    __tablename__ = 'algorithm_post_process_result'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, nullable=False, index=True, comment='算法任务ID')
    task_name = db.Column(db.String(255), nullable=True, comment='任务名称')
    task_code = db.Column(db.String(255), nullable=True, comment='任务编号')
    task_type = db.Column(db.String(20), nullable=True, comment='任务类型[realtime,snap,patrol]')
    device_id = db.Column(db.String(100), nullable=False, index=True, comment='设备ID')
    device_name = db.Column(db.String(100), nullable=True, comment='设备名称')
    frame_number = db.Column(db.Integer, nullable=True, comment='帧序号')
    event_time = db.Column(db.DateTime(timezone=True), nullable=True, index=True, comment='帧事件时间')
    counts = db.Column(db.Text, nullable=True, comment='计数结果 JSON')
    events = db.Column(db.Text, nullable=True, comment='业务事件 JSON')
    alerts = db.Column(db.Text, nullable=True, comment='自定义告警 JSON')
    payload = db.Column(db.Text, nullable=True, comment='完整后处理结果 JSON')
    correlation_id = db.Column(db.String(36), nullable=True, index=True, comment='关联ID（去重/追溯）')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), index=True)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'task_code': self.task_code,
            'task_type': self.task_type,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'frame_number': self.frame_number,
            'event_time': utc_isoformat_z(self.event_time),
            'counts': json.loads(self.counts) if self.counts else None,
            'events': json.loads(self.events) if self.events else None,
            'alerts': json.loads(self.alerts) if self.alerts else None,
            'payload': json.loads(self.payload) if self.payload else None,
            'correlation_id': self.correlation_id,
            'created_at': utc_isoformat_z(self.created_at),
        }


class FaceLibrary(db.Model):
    """人脸库（支持业务标签，供算法任务人脸匹配使用）"""
    __tablename__ = 'face_library'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, comment='人脸库名称')
    code = db.Column(db.String(100), nullable=False, unique=True, comment='人脸库编码（唯一）')
    business_tags = db.Column(db.Text, nullable=True, comment='业务标签（JSON数组，如["员工","访客"]）')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    similarity_threshold = db.Column(db.Float, default=0.55, nullable=False, comment='默认匹配相似度阈值')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    face_count = db.Column(db.Integer, default=0, nullable=False, comment='人脸数量（冗余统计）')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    entries = db.relationship('FaceEntry', backref='library', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_entries: bool = False):
        import json
        tags = []
        if self.business_tags:
            try:
                tags = json.loads(self.business_tags) if isinstance(self.business_tags, str) else self.business_tags
            except Exception:
                tags = []
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'business_tags': tags,
            'description': self.description,
            'similarity_threshold': self.similarity_threshold,
            'is_enabled': self.is_enabled,
            'face_count': self.face_count,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }
        if include_entries:
            data['entries'] = [e.to_dict() for e in (self.entries or [])]
        return data


class FacePerson(db.Model):
    """归一化后的人员（可包含多张人脸照片）"""
    __tablename__ = 'face_person'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    library_id = db.Column(db.Integer, db.ForeignKey('face_library.id', ondelete='CASCADE'), nullable=False, comment='所属人脸库ID')
    person_name = db.Column(db.String(255), nullable=False, comment='人员姓名')
    person_code = db.Column(db.String(100), nullable=True, comment='人员编号/工号')
    cover_entry_id = db.Column(db.Integer, nullable=True, comment='封面人脸条目ID')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    face_count = db.Column(db.Integer, default=1, nullable=False, comment='关联人脸照片数')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    entries = db.relationship('FaceEntry', backref='person', lazy=True, foreign_keys='FaceEntry.person_id')

    def to_dict(self, include_entries: bool = False, cover_image_url: str = None):
        data = {
            'id': self.id,
            'library_id': self.library_id,
            'person_name': self.person_name,
            'person_code': self.person_code,
            'cover_entry_id': self.cover_entry_id,
            'cover_image_url': cover_image_url,
            'is_enabled': self.is_enabled,
            'face_count': self.face_count,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }
        if include_entries:
            data['entries'] = [e.to_dict() for e in (self.entries or [])]
        return data


class FaceEntry(db.Model):
    """人脸库中的人脸条目"""
    __tablename__ = 'face_entry'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    library_id = db.Column(db.Integer, db.ForeignKey('face_library.id', ondelete='CASCADE'), nullable=False, comment='所属人脸库ID')
    person_id = db.Column(db.Integer, db.ForeignKey('face_person.id', ondelete='CASCADE'), nullable=True, comment='所属归一化人员ID')
    person_name = db.Column(db.String(255), nullable=False, comment='人员姓名')
    person_code = db.Column(db.String(100), nullable=True, comment='人员编号/工号')
    image_path = db.Column(db.String(500), nullable=True, comment='人脸图片本地路径')
    image_url = db.Column(db.String(500), nullable=True, comment='人脸图片URL（MinIO）')
    milvus_id = db.Column(db.String(64), nullable=True, comment='Milvus向量ID')
    remark = db.Column(db.String(500), nullable=True, comment='备注')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def to_dict(self):
        return {
            'id': self.id,
            'library_id': self.library_id,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'person_code': self.person_code,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'milvus_id': self.milvus_id,
            'remark': self.remark,
            'is_enabled': self.is_enabled,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }


class FaceAutoEnrollTask(db.Model):
    """人脸库自动录入任务（绑定摄像头，限时采集新人脸）"""
    __tablename__ = 'face_auto_enroll_task'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    library_id = db.Column(
        db.Integer, db.ForeignKey('face_library.id', ondelete='CASCADE'),
        nullable=False, unique=True, comment='所属人脸库ID',
    )
    device_ids = db.Column(db.Text, nullable=False, default='[]', comment='绑定的摄像头ID列表（JSON数组）')
    duration_minutes = db.Column(db.Integer, default=60, nullable=False, comment='录入模式开启时长（分钟）')
    capture_interval_sec = db.Column(db.Integer, default=5, nullable=False, comment='抓帧间隔（秒）')
    person_name_prefix = db.Column(db.String(50), default='自动录入', nullable=False, comment='自动命名前缀')
    is_running = db.Column(db.Boolean, default=False, nullable=False, comment='是否正在运行')
    started_at = db.Column(db.DateTime, nullable=True, comment='本次启动时间')
    expires_at = db.Column(db.DateTime, nullable=True, comment='本次到期时间')
    enrolled_count = db.Column(db.Integer, default=0, nullable=False, comment='本次已录入数量')
    skipped_count = db.Column(db.Integer, default=0, nullable=False, comment='本次跳过数量（已存在或重复）')
    last_device_index = db.Column(db.Integer, default=0, nullable=False, comment='轮询摄像头索引')
    last_tick_at = db.Column(db.DateTime, nullable=True, comment='上次抓帧时间')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    library = db.relationship('FaceLibrary', backref=db.backref('auto_enroll_task', uselist=False), lazy=True)

    def to_dict(self):
        import json
        device_ids = []
        try:
            device_ids = json.loads(self.device_ids) if isinstance(self.device_ids, str) else (self.device_ids or [])
        except Exception:
            device_ids = []
        device_names = []
        if device_ids:
            devices = Device.query.filter(Device.id.in_(device_ids)).all()
            name_map = {d.id: d.name for d in devices}
            device_names = [name_map.get(did, did) for did in device_ids]
        return {
            'id': self.id,
            'library_id': self.library_id,
            'device_ids': device_ids,
            'device_names': device_names,
            'duration_minutes': self.duration_minutes,
            'capture_interval_sec': self.capture_interval_sec,
            'person_name_prefix': self.person_name_prefix,
            'is_running': self.is_running,
            'started_at': utc_isoformat_z(self.started_at),
            'expires_at': utc_isoformat_z(self.expires_at),
            'enrolled_count': self.enrolled_count,
            'skipped_count': self.skipped_count,
            'last_device_index': self.last_device_index,
            'last_tick_at': utc_isoformat_z(self.last_tick_at),
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }


class FaceMatchRecord(db.Model):
    """人脸匹配记录（Kafka消费端写入）"""
    __tablename__ = 'face_match_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, nullable=True, comment='算法任务ID')
    task_name = db.Column(db.String(255), nullable=True, comment='算法任务名称')
    device_id = db.Column(db.String(100), nullable=False, comment='设备ID')
    device_name = db.Column(db.String(255), nullable=True, comment='设备名称')
    library_id = db.Column(db.Integer, nullable=True, comment='人脸库ID')
    library_name = db.Column(db.String(255), nullable=True, comment='人脸库名称')
    face_image_path = db.Column(db.String(500), nullable=True, comment='待匹配人脸图片路径')
    matched = db.Column(db.Boolean, default=False, nullable=False, comment='是否匹配成功')
    matched_person_name = db.Column(db.String(255), nullable=True, comment='匹配到的人员姓名')
    matched_person_code = db.Column(db.String(100), nullable=True, comment='匹配到的人员编号')
    matched_face_entry_id = db.Column(db.Integer, nullable=True, comment='匹配到的人脸条目ID')
    similarity = db.Column(db.Float, nullable=True, comment='最高相似度')
    threshold = db.Column(db.Float, nullable=True, comment='使用的阈值')
    candidates = db.Column(db.Text, nullable=True, comment='候选结果（JSON）')
    alert_id = db.Column(db.Integer, nullable=True, comment='库匹配命中后新建的告警ID')
    correlation_id = db.Column(db.String(36), nullable=True, index=True, comment='关联事件ID（与算法告警同一帧）')
    task_type = db.Column(db.String(20), nullable=True, comment='任务类型')
    status = db.Column(db.String(20), default='pending', nullable=False, comment='处理状态[pending,success,failed]')
    error_message = db.Column(db.String(500), nullable=True, comment='错误信息')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    def to_dict(self):
        import json
        candidates = None
        if self.candidates:
            try:
                candidates = json.loads(self.candidates) if isinstance(self.candidates, str) else self.candidates
            except Exception:
                candidates = self.candidates
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'library_id': self.library_id,
            'library_name': self.library_name,
            'face_image_path': self.face_image_path,
            'matched': self.matched,
            'matched_person_name': self.matched_person_name,
            'matched_person_code': self.matched_person_code,
            'matched_face_entry_id': self.matched_face_entry_id,
            'similarity': self.similarity,
            'threshold': self.threshold,
            'candidates': candidates,
            'alert_id': self.alert_id,
            'correlation_id': self.correlation_id,
            'task_type': self.task_type,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': utc_isoformat_z(self.created_at),
        }


class PlateLibrary(db.Model):
    """车牌库（供算法任务车牌匹配使用）"""
    __tablename__ = 'plate_library'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, comment='车牌库名称')
    code = db.Column(db.String(100), nullable=False, unique=True, comment='车牌库编码（唯一）')
    business_tags = db.Column(db.Text, nullable=True, comment='业务标签（JSON数组）')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    plate_count = db.Column(db.Integer, default=0, nullable=False, comment='车牌数量（冗余统计）')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    entries = db.relationship('PlateEntry', backref='library', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_entries: bool = False):
        import json
        tags = []
        if self.business_tags:
            try:
                tags = json.loads(self.business_tags) if isinstance(self.business_tags, str) else self.business_tags
            except Exception:
                tags = []
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'business_tags': tags,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'plate_count': self.plate_count,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }
        if include_entries:
            data['entries'] = [e.to_dict() for e in (self.entries or [])]
        return data


class PlateEntry(db.Model):
    """车牌库中的车牌条目"""
    __tablename__ = 'plate_entry'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    library_id = db.Column(db.Integer, db.ForeignKey('plate_library.id', ondelete='CASCADE'), nullable=False, comment='所属车牌库ID')
    plate_no = db.Column(db.String(20), nullable=False, comment='车牌号码')
    plate_color = db.Column(db.String(20), nullable=True, comment='车牌颜色')
    owner_name = db.Column(db.String(255), nullable=True, comment='车主姓名')
    owner_phone = db.Column(db.String(50), nullable=True, comment='车主电话')
    image_path = db.Column(db.String(500), nullable=True, comment='车牌图片本地路径')
    image_url = db.Column(db.String(500), nullable=True, comment='车牌图片URL（MinIO）')
    remark = db.Column(db.String(500), nullable=True, comment='备注')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def to_dict(self):
        return {
            'id': self.id,
            'library_id': self.library_id,
            'plate_no': self.plate_no,
            'plate_color': self.plate_color,
            'owner_name': self.owner_name,
            'owner_phone': self.owner_phone,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'remark': self.remark,
            'is_enabled': self.is_enabled,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }


class PlateAutoEnrollTask(db.Model):
    """车牌库自动录入任务（绑定摄像头，限时采集新车牌）"""
    __tablename__ = 'plate_auto_enroll_task'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    library_id = db.Column(
        db.Integer, db.ForeignKey('plate_library.id', ondelete='CASCADE'),
        nullable=False, unique=True, comment='所属车牌库ID',
    )
    device_ids = db.Column(db.Text, nullable=False, default='[]', comment='绑定的摄像头ID列表（JSON数组）')
    duration_minutes = db.Column(db.Integer, default=60, nullable=False, comment='录入模式开启时长（分钟）')
    capture_interval_sec = db.Column(db.Integer, default=5, nullable=False, comment='抓帧间隔（秒）')
    is_running = db.Column(db.Boolean, default=False, nullable=False, comment='是否正在运行')
    started_at = db.Column(db.DateTime, nullable=True, comment='本次启动时间')
    expires_at = db.Column(db.DateTime, nullable=True, comment='本次到期时间')
    enrolled_count = db.Column(db.Integer, default=0, nullable=False, comment='本次已录入数量')
    skipped_count = db.Column(db.Integer, default=0, nullable=False, comment='本次跳过数量（已存在或重复）')
    last_device_index = db.Column(db.Integer, default=0, nullable=False, comment='轮询摄像头索引')
    last_tick_at = db.Column(db.DateTime, nullable=True, comment='上次抓帧时间')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    library = db.relationship('PlateLibrary', backref=db.backref('auto_enroll_task', uselist=False), lazy=True)

    def to_dict(self):
        import json
        device_ids = []
        try:
            device_ids = json.loads(self.device_ids) if isinstance(self.device_ids, str) else (self.device_ids or [])
        except Exception:
            device_ids = []
        device_names = []
        if device_ids:
            devices = Device.query.filter(Device.id.in_(device_ids)).all()
            name_map = {d.id: d.name for d in devices}
            device_names = [name_map.get(did, did) for did in device_ids]
        return {
            'id': self.id,
            'library_id': self.library_id,
            'device_ids': device_ids,
            'device_names': device_names,
            'duration_minutes': self.duration_minutes,
            'capture_interval_sec': self.capture_interval_sec,
            'is_running': self.is_running,
            'started_at': utc_isoformat_z(self.started_at),
            'expires_at': utc_isoformat_z(self.expires_at),
            'enrolled_count': self.enrolled_count,
            'skipped_count': self.skipped_count,
            'last_device_index': self.last_device_index,
            'last_tick_at': utc_isoformat_z(self.last_tick_at),
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }


class PlateMatchRecord(db.Model):
    """车牌匹配记录（Kafka消费端写入）"""
    __tablename__ = 'plate_match_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, nullable=True, comment='算法任务ID')
    task_name = db.Column(db.String(255), nullable=True, comment='算法任务名称')
    device_id = db.Column(db.String(100), nullable=False, comment='设备ID')
    device_name = db.Column(db.String(255), nullable=True, comment='设备名称')
    library_id = db.Column(db.Integer, nullable=True, comment='车牌库ID')
    library_name = db.Column(db.String(255), nullable=True, comment='车牌库名称')
    plate_no = db.Column(db.String(20), nullable=True, comment='识别出的车牌号')
    plate_color = db.Column(db.String(20), nullable=True, comment='识别出的车牌颜色')
    plate_image_path = db.Column(db.String(500), nullable=True, comment='车牌裁剪图路径')
    matched = db.Column(db.Boolean, default=False, nullable=False, comment='是否在库中匹配成功')
    matched_plate_entry_id = db.Column(db.Integer, nullable=True, comment='匹配到的车牌条目ID')
    matched_owner_name = db.Column(db.String(255), nullable=True, comment='匹配到的车主姓名')
    detect_conf = db.Column(db.Float, nullable=True, comment='识别置信度')
    alert_id = db.Column(db.Integer, nullable=True, comment='库匹配命中后新建的告警ID')
    correlation_id = db.Column(db.String(36), nullable=True, index=True, comment='关联事件ID（与算法告警同一帧）')
    task_type = db.Column(db.String(20), nullable=True, comment='任务类型')
    status = db.Column(db.String(20), default='pending', nullable=False, comment='处理状态[pending,success,failed]')
    error_message = db.Column(db.String(500), nullable=True, comment='错误信息')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'library_id': self.library_id,
            'library_name': self.library_name,
            'plate_no': self.plate_no,
            'plate_color': self.plate_color,
            'plate_image_path': self.plate_image_path,
            'matched': self.matched,
            'matched_plate_entry_id': self.matched_plate_entry_id,
            'matched_owner_name': self.matched_owner_name,
            'detect_conf': self.detect_conf,
            'alert_id': self.alert_id,
            'correlation_id': self.correlation_id,
            'task_type': self.task_type,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': utc_isoformat_z(self.created_at),
        }


class ScenarioPoseLibrary(db.Model):
    """场景姿态库（供算法任务姿态意图分析使用）"""
    __tablename__ = 'scenario_pose_library'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, comment='场景姿态库名称')
    code = db.Column(db.String(100), nullable=False, unique=True, comment='库编码（唯一）')
    scene_category = db.Column(db.String(50), nullable=True, comment='场景类别 fall/climb/squat/hands_up/custom')
    business_tags = db.Column(db.Text, nullable=True, comment='业务标签 JSON 数组')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    similarity_threshold = db.Column(db.Float, default=0.72, nullable=False, comment='默认匹配阈值')
    match_mode = db.Column(db.String(30), default='angle', nullable=False, comment='匹配模式 angle/ratio/combined')
    intent_event = db.Column(db.String(100), nullable=True, comment='命中告警 event')
    intent_object = db.Column(db.String(100), nullable=True, comment='命中告警 object')
    alert_level = db.Column(db.String(20), default='warning', nullable=False, comment='告警级别')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    entry_count = db.Column(db.Integer, default=0, nullable=False, comment='条目数量')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    entries = db.relationship(
        'ScenarioPoseEntry', backref='library', lazy=True, cascade='all, delete-orphan',
    )

    def to_dict(self, include_entries: bool = False):
        import json
        tags = []
        if self.business_tags:
            try:
                tags = json.loads(self.business_tags) if isinstance(self.business_tags, str) else self.business_tags
            except Exception:
                tags = []
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'scene_category': self.scene_category,
            'business_tags': tags,
            'description': self.description,
            'similarity_threshold': self.similarity_threshold,
            'match_mode': self.match_mode,
            'intent_event': self.intent_event,
            'intent_object': self.intent_object,
            'alert_level': self.alert_level,
            'is_enabled': self.is_enabled,
            'entry_count': self.entry_count,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }
        if include_entries:
            data['entries'] = [e.to_dict() for e in (self.entries or [])]
        return data


class ScenarioPoseEntry(db.Model):
    """场景姿态库条目（参考姿态模板）"""
    __tablename__ = 'scenario_pose_entry'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    library_id = db.Column(
        db.Integer, db.ForeignKey('scenario_pose_library.id', ondelete='CASCADE'),
        nullable=False, comment='所属场景姿态库ID',
    )
    name = db.Column(db.String(255), nullable=False, comment='条目名称')
    source_type = db.Column(db.String(20), default='image', nullable=False, comment='来源 image/rule/manual')
    image_path = db.Column(db.String(500), nullable=True, comment='参考图本地路径')
    image_url = db.Column(db.String(500), nullable=True, comment='参考图 URL')
    keypoints = db.Column(db.Text, nullable=True, comment='COCO-17 关键点 JSON')
    feature_vector = db.Column(db.Text, nullable=True, comment='归一化特征向量 JSON')
    keypoint_visibility_min = db.Column(db.Float, default=0.3, nullable=False)
    extra_rules = db.Column(db.Text, nullable=True, comment='附加规则 JSON')
    remark = db.Column(db.String(500), nullable=True, comment='备注')
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def to_dict(self):
        import json
        kps = None
        if self.keypoints:
            try:
                kps = json.loads(self.keypoints) if isinstance(self.keypoints, str) else self.keypoints
            except Exception:
                kps = None
        rules = None
        if self.extra_rules:
            try:
                rules = json.loads(self.extra_rules) if isinstance(self.extra_rules, str) else self.extra_rules
            except Exception:
                rules = None
        feat = None
        if self.feature_vector:
            try:
                feat = json.loads(self.feature_vector) if isinstance(self.feature_vector, str) else self.feature_vector
            except Exception:
                feat = None
        return {
            'id': self.id,
            'library_id': self.library_id,
            'name': self.name,
            'source_type': self.source_type,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'keypoints': kps,
            'feature_vector': feat,
            'keypoint_visibility_min': self.keypoint_visibility_min,
            'extra_rules': rules,
            'remark': self.remark,
            'is_enabled': self.is_enabled,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }


class PoseIntentMatchRecord(db.Model):
    """姿态意图匹配记录"""
    __tablename__ = 'pose_intent_match_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, nullable=True, comment='算法任务ID')
    task_name = db.Column(db.String(255), nullable=True)
    device_id = db.Column(db.String(100), nullable=False, index=True)
    device_name = db.Column(db.String(255), nullable=True)
    library_id = db.Column(db.Integer, nullable=True)
    library_name = db.Column(db.String(255), nullable=True)
    entry_id = db.Column(db.Integer, nullable=True)
    entry_name = db.Column(db.String(255), nullable=True)
    similarity = db.Column(db.Float, nullable=True)
    intent_event = db.Column(db.String(100), nullable=True)
    matched = db.Column(db.Boolean, default=False, nullable=False)
    pose_snapshot = db.Column(db.Text, nullable=True, comment='命中时关键点 JSON')
    alert_id = db.Column(db.Integer, nullable=True)
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    task_type = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    def to_dict(self):
        import json
        snapshot = None
        if self.pose_snapshot:
            try:
                snapshot = json.loads(self.pose_snapshot) if isinstance(self.pose_snapshot, str) else self.pose_snapshot
            except Exception:
                snapshot = None
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'library_id': self.library_id,
            'library_name': self.library_name,
            'entry_id': self.entry_id,
            'entry_name': self.entry_name,
            'similarity': self.similarity,
            'intent_event': self.intent_event,
            'matched': self.matched,
            'pose_snapshot': snapshot,
            'alert_id': self.alert_id,
            'correlation_id': self.correlation_id,
            'task_type': self.task_type,
            'created_at': utc_isoformat_z(self.created_at),
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
    # MinIO 下载 API 等完整路径可能较长
    file_path = db.Column(db.String(500), nullable=False)  # 文件路径
    event_time = db.Column(db.DateTime(timezone=True), nullable=False)  # 录制发生时间
    device_id = db.Column(db.String(100), nullable=False)  # 设备id（与 device.id 一致）
    device_name = db.Column(db.String(100), nullable=False)  # 设备名称
    duration = db.Column(db.SmallInteger(), nullable=False)  # 时长/秒
    thumbnail_path = db.Column(db.String(500), nullable=True)  # 封面图路径
    file_size = db.Column(db.BigInteger(), nullable=True)  # 文件大小（字节）
    # 使用带时区的本地时间（Asia/Shanghai，UTC+8）
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=8))))  # 创建时间
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=8))), onupdate=lambda: datetime.now(timezone(timedelta(hours=8))))  # 更新时间
    
    def to_dict(self):
        """转换为字典"""
        from app.utils.service_urls import resolve_playback_display_url
        file_path = self.file_path or ''
        return {
            'id': self.id,
            'file_path': file_path,
            'video_url': resolve_playback_display_url(file_path),
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
    service_server_ip = db.Column(db.String(512), nullable=True, comment='服务运行服务器IP（多节点时为逗号分隔）')
    service_port = db.Column(db.Integer, nullable=True, comment='服务端口')
    service_process_id = db.Column(db.Integer, nullable=True, comment='服务进程ID')
    service_last_heartbeat = db.Column(db.DateTime, nullable=True, comment='服务最后心跳时间')
    service_log_path = db.Column(db.String(500), nullable=True, comment='服务日志路径')

    # 节点调度（跨节点部署）
    schedule_policy = db.Column(db.String(20), default='local', nullable=False,
                                comment='调度策略[local:本机,auto:自动节点,node:指定节点]')
    prefer_gpu = db.Column(db.Boolean, default=True, nullable=False,
                           comment='自动调度时是否优先 GPU 节点')
    target_node_id = db.Column(db.BigInteger, nullable=True, comment='指定部署节点ID')
    node_id = db.Column(db.BigInteger, nullable=True, comment='实际运行节点ID（单节点部署）')
    device_deployments = db.Column(db.Text, nullable=True,
                                   comment='设备级远程部署明细 JSON：[{device_ids,node_id,host,workload_id,pid}]')

    # 执行后端：cpp=RUNTIME forward 直通（高性能，默认）；python=FFmpeg 推流
    executor = db.Column(db.String(20), default='cpp', nullable=False,
                         comment='执行后端[cpp:RUNTIME forward,python:FFmpeg]')
    runtime_bin_path = db.Column(db.String(500), nullable=True, comment='自定义 RUNTIME 二进制路径')
    
    # 统计信息
    total_streams = db.Column(db.Integer, default=0, nullable=False, comment='总推流数')
    last_process_time = db.Column(db.DateTime, nullable=True, comment='最后处理时间')
    last_success_time = db.Column(db.DateTime, nullable=True, comment='最后成功时间')
    
    description = db.Column(db.String(500), nullable=True, comment='任务描述')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关联关系
    devices = db.relationship('Device', secondary=stream_forward_task_device, backref='stream_forward_task_list', lazy=True)  # 多对多关系

    def _parse_device_deployments(self):
        import json
        raw = self.device_deployments
        if not raw:
            return []
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data if isinstance(data, list) else []
        except Exception:
            return []
    
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
            'service_last_heartbeat': utc_isoformat_z(self.service_last_heartbeat),
            'service_log_path': self.service_log_path,
            'schedule_policy': self.schedule_policy,
            'prefer_gpu': self.prefer_gpu if self.prefer_gpu is not None else True,
            'target_node_id': self.target_node_id,
            'node_id': self.node_id,
            'executor': getattr(self, 'executor', None) or 'cpp',
            'runtime_bin_path': getattr(self, 'runtime_bin_path', None),
            'device_deployments': self._parse_device_deployments(),
            'total_streams': self.total_streams,
            'last_process_time': utc_isoformat_z(self.last_process_time),
            'last_success_time': utc_isoformat_z(self.last_success_time),
            'description': self.description,
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at)
        }


class PatrolSession(db.Model):
    """摄像头巡检会话（分屏监控临时或计划性 AI 分析）"""
    __tablename__ = 'patrol_session'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_name = db.Column(db.String(255), nullable=False, comment='会话名称')
    patrol_mode = db.Column(db.String(20), default='pool', nullable=False,
                            comment='巡检模式[rotate:轮询,pool:连接池,hybrid:混合]')
    interval_sec = db.Column(db.Integer, default=10, nullable=False, comment='每路巡检间隔（秒）')
    pool_size = db.Column(db.Integer, default=4, nullable=False, comment='连接池并发拉流数（pool/hybrid）')
    device_ids = db.Column(db.Text, nullable=False, comment='设备ID列表（JSON数组）')
    model_ids = db.Column(db.Text, nullable=False, comment='模型ID列表（JSON数组）')
    focus_device_id = db.Column(db.String(100), nullable=True, comment='焦点设备ID（hybrid）')
    algorithm_task_id = db.Column(db.Integer, nullable=True, comment='关联算法任务模板ID')

    alert_event_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用告警')
    alert_event_suppress_time = db.Column(db.Integer, default=5, nullable=False, comment='告警抑制间隔（秒）')
    face_detection_enabled = db.Column(db.Boolean, default=True, nullable=False)
    plate_detection_enabled = db.Column(db.Boolean, default=True, nullable=False)

    status = db.Column(db.String(20), default='stopped', nullable=False,
                       comment='状态[running,stopped,error]')
    exception_reason = db.Column(db.String(500), nullable=True)
    service_server_ip = db.Column(db.String(512), nullable=True)
    service_process_id = db.Column(db.Integer, nullable=True)
    service_last_heartbeat = db.Column(db.DateTime, nullable=True)
    service_log_path = db.Column(db.String(500), nullable=True)
    progress_json = db.Column(db.Text, nullable=True, comment='每设备巡检进度（JSON）')

    total_patrols = db.Column(db.Integer, default=0, nullable=False, comment='累计巡检次数')
    total_detections = db.Column(db.Integer, default=0, nullable=False, comment='累计检测次数')
    last_patrol_time = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    @staticmethod
    def _parse_json_list(raw):
        import json
        if not raw:
            return []
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def to_dict(self):
        import json
        device_ids = self._parse_json_list(self.device_ids)
        model_ids = self._parse_json_list(self.model_ids)
        progress = {}
        if self.progress_json:
            try:
                progress = json.loads(self.progress_json) if isinstance(self.progress_json, str) else self.progress_json
            except Exception:
                progress = {}
        device_names = []
        if device_ids:
            devices = Device.query.filter(Device.id.in_(device_ids)).all()
            name_map = {d.id: d.name or d.id for d in devices}
            device_names = [name_map.get(did, did) for did in device_ids]
        return {
            'id': self.id,
            'session_name': self.session_name,
            'patrol_mode': self.patrol_mode,
            'interval_sec': self.interval_sec,
            'pool_size': self.pool_size,
            'device_ids': device_ids,
            'device_names': device_names,
            'model_ids': model_ids,
            'focus_device_id': self.focus_device_id,
            'algorithm_task_id': self.algorithm_task_id,
            'alert_event_enabled': self.alert_event_enabled,
            'alert_event_suppress_time': self.alert_event_suppress_time,
            'face_detection_enabled': self.face_detection_enabled,
            'plate_detection_enabled': self.plate_detection_enabled,
            'status': self.status,
            'exception_reason': self.exception_reason,
            'service_server_ip': self.service_server_ip,
            'service_process_id': self.service_process_id,
            'service_last_heartbeat': utc_isoformat_z(self.service_last_heartbeat),
            'service_log_path': self.service_log_path,
            'progress': progress,
            'total_patrols': self.total_patrols,
            'total_detections': self.total_detections,
            'last_patrol_time': utc_isoformat_z(self.last_patrol_time),
            'created_at': utc_isoformat_z(self.created_at),
            'updated_at': utc_isoformat_z(self.updated_at),
        }


def ensure_algorithm_task_sam_columns(engine):
    """老库 algorithm_task 表补 SAM 补充识别列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'sam_supplement_enabled': 'BOOLEAN DEFAULT FALSE',
        'sam_supplement_config': 'TEXT',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_sam_columns: %s', e)


def ensure_algorithm_task_pose_columns(engine):
    """老库 algorithm_task 表补人体姿态分析列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'pose_analysis_enabled': 'BOOLEAN DEFAULT FALSE',
        'pose_analysis_config': 'TEXT',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_pose_columns: %s', e)


def ensure_algorithm_task_post_process_columns(engine):
    """老库 algorithm_task 表补 AI 后处理列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'post_process_enabled': 'BOOLEAN DEFAULT FALSE',
        'post_process_script': 'VARCHAR(255)',
        'post_process_replicas': 'INTEGER DEFAULT 1',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_post_process_columns: %s', e)


def ensure_stream_forward_task_executor_columns(engine):
    """老库 stream_forward_task 表补 RUNTIME/cpp 执行后端列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'executor': "VARCHAR(20) DEFAULT 'cpp'",
        'runtime_bin_path': 'VARCHAR(500)',
    }
    try:
        inspector = inspect(engine)
        if 'stream_forward_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('stream_forward_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE stream_forward_task ADD COLUMN {col} {ddl}'))
            log.info('已为 stream_forward_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_stream_forward_task_executor_columns: %s', e)


def ensure_algorithm_task_executor_columns(engine):
    """老库 algorithm_task 表补 RUNTIME/cpp 执行后端列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'executor': "VARCHAR(20) DEFAULT 'cpp'",
        'runtime_bin_path': 'VARCHAR(500)',
        'runtime_control_port': 'INTEGER',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_executor_columns: %s', e)


def ensure_algorithm_task_detect_conf_column(engine):
    """老库 algorithm_task 表补 YOLO 检测置信度列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'detect_conf': 'DOUBLE PRECISION DEFAULT 0.5',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_detect_conf_column: %s', e)


def ensure_algorithm_task_pose_intent_columns(engine):
    """老库 algorithm_task 表补姿态意图分析列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'pose_intent_enabled': 'BOOLEAN DEFAULT FALSE',
        'pose_library_ids': 'TEXT',
        'pose_intent_threshold': 'DOUBLE PRECISION',
        'pose_intent_config': 'TEXT',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_pose_intent_columns: %s', e)


def ensure_algorithm_task_alert_class_columns(engine):
    """老库 algorithm_task 表补告警触发类别标签列。"""
    import logging
    from sqlalchemy import inspect, text

    log = logging.getLogger(__name__)
    columns = {
        'alert_class_names': 'TEXT',
    }
    try:
        inspector = inspect(engine)
        if 'algorithm_task' not in inspector.get_table_names():
            return
        col_names = {c['name'] for c in inspector.get_columns('algorithm_task')}
        for col, ddl in columns.items():
            if col in col_names:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE algorithm_task ADD COLUMN {col} {ddl}'))
            log.info('已为 algorithm_task 表添加 %s 列', col)
    except Exception as e:
        log.warning('ensure_algorithm_task_alert_class_columns: %s', e)
