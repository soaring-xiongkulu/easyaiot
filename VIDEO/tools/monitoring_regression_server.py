"""Loopback integration fixture: production VIDEO models/routes + real POST/MQTT.

Uses a separate SQLite file. Camera pixels and tracked detections are generated
fixtures; the alert subscriber substitutes for Java iot-sink only in this profile.
Never import this module from production run.py.
"""
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('POST_BASE_URL', 'http://127.0.0.1:19090')
os.environ['CAMERA_SOURCE_MODE'] = 'direct'
os.environ['ALGO_BUS_TRANSPORT'] = 'off'
# 生产 trainframe 路由经 algo_mqtt_bus._brokers() 发现 broker，隔离环境指向本地 18883
os.environ.setdefault('MQTT_BROKER_URLS', '127.0.0.1:18883')

from flask import Flask, jsonify, request, send_file
from PIL import Image as PILImage, ImageDraw
import numpy as np
import paho.mqtt.client as mqtt
from models import db, AlgorithmTask, Device, Image, Alert, DeviceDetectionRegion
from app.blueprints import post_plugin, device_detection_region, algorithm_task, camera

WORK = Path(
    os.environ.get('MONITORING_REGRESSION_WORK')
    or (Path(tempfile.gettempdir()) / 'easyaiot-monitoring-integration')
)
WORK.mkdir(exist_ok=True)
app = Flask(__name__)
app.config.update(SQLALCHEMY_DATABASE_URI=f'sqlite:///{(WORK / "video.sqlite").as_posix()}', SQLALCHEMY_TRACK_MODIFICATIONS=False)
db.init_app(app)
FAIL_NEXT_SAVE = False


@app.before_request
def failure_fixture():
    global FAIL_NEXT_SAVE
    if FAIL_NEXT_SAVE and request.method == 'PUT' and ('/binding' in request.path or request.path.endswith('/regions')):
        FAIL_NEXT_SAVE = False
        return jsonify({'code':503,'msg':'测试注入：暂时保存失败，未写入数据，可直接重试'}),503


def camera_frame(device_id):
    image = PILImage.new('RGB', (1280, 720), '#dbe8f2')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 180), fill='#849eb5')
    draw.rectangle((120, 200, 1160, 650), fill='#f5f0dd', outline='#526c80', width=10)
    draw.rectangle((480, 30, 800, 210), fill='#58798c')
    draw.rectangle((150, 450, 380, 620), fill='#a0bca7')
    draw.rectangle((900, 450, 1130, 620), fill='#b9d5a7')
    draw.text((480, 330), f'ISOLATED TEST CAMERA: {device_id}', fill='#314558')
    return image


def fixture_upload(device_id, frame, extension):
    url = f'/dev-api/video/regression/frame/{device_id}.png'
    filename = f'{device_id}.png'
    db.session.add(Image(
        device_id=device_id,
        filename=filename,
        original_filename=filename,
        path=url,
        width=1280,
        height=720,
    ))
    db.session.commit()
    return url


# Replace only external capture/storage transports; all business routes stay real.
device_detection_region.grab_frame_for_snapshot = lambda device: (np.array(camera_frame(device.id)), None)
device_detection_region.upload_screenshot_to_minio = fixture_upload
algorithm_task._camera_source_status_map = lambda: {}
camera.camera_service.ensure_device_spaces = lambda _device_id: None
app.register_blueprint(camera.camera_bp, url_prefix='/video/camera')
app.register_blueprint(algorithm_task.algorithm_task_bp, url_prefix='/video/algorithm')
app.register_blueprint(device_detection_region.device_detection_region_bp, url_prefix='/video/device-detection')
app.register_blueprint(post_plugin.post_plugin_bp, url_prefix='/video/post')

with app.app_context():
    db.create_all()
    if AlgorithmTask.query.get(1) is None:
        devices = []
        for device_id, name in [('regression-a', '正门摄像头'), ('regression-b', '后门摄像头')]:
            dev = Device(id=device_id, name=name, source=f'regression://{device_id}', manufacturer='regression', model='test-camera', rtmp_stream='', http_stream='', cover_image_path=f'/dev-api/video/regression/frame/{device_id}.png')
            devices.append(dev)
            db.session.add(dev)
        task = AlgorithmTask(id=1, task_code='isolated-monitoring-regression', task_name='本地监测回归任务', task_type='realtime', executor='python', model_ids='[1]', model_names='回归行人模型', tracking_enabled=True, alert_event_enabled=True, face_detection_enabled=False, is_enabled=True, run_status='running', template_revision=1)
        task.devices = devices
        db.session.add(task)
        db.session.commit()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='regression-alert-sink')


def on_connect(c, _userdata, _flags, reason_code, _properties):
    if reason_code == 0:
        c.subscribe('mqtt/iot-alert-notification', 1)


def on_message(_client, _userdata, message):
    payload = json.loads(message.payload)
    with app.app_context():
        correlation = payload.get('correlation_id') or payload.get('correlationId')
        if Alert.query.filter_by(correlation_id=correlation).first():
            return
        alert = payload['alert']
        db.session.add(Alert(object=alert.get('object', '')[:30], event=alert.get('event', '')[:30], region=alert.get('region', '')[:30], information=json.dumps(alert.get('information', {}), ensure_ascii=False), time=datetime.now(timezone.utc), task_id=int(payload['task_id']), device_id=payload['device_id'], device_name=payload.get('device_name', ''), task_type='realtime', correlation_id=correlation))
        db.session.commit()


client.on_connect = on_connect
client.on_message = on_message


@app.get('/video/regression/frame/<device_id>.png')
def frame(device_id):
    data = io.BytesIO()
    camera_frame(device_id).save(data, format='PNG')
    data.seek(0)
    return send_file(data, mimetype='image/png', max_age=0)


@app.get('/video/regression/state')
def state():
    task = AlgorithmTask.query.get(1)
    return jsonify({'task': task.to_dict(), 'regions': [r.to_dict() for r in DeviceDetectionRegion.query.all()], 'alerts': Alert.query.count()})


@app.post('/video/regression/scenario')
def scenario():
    global FAIL_NEXT_SAVE
    data = request.get_json() or {}
    device_id, kind = data.get('device_id', 'regression-a'), data.get('kind')
    task = AlgorithmTask.query.get(1)
    if kind == 'fail_save':
        FAIL_NEXT_SAVE = True
        return jsonify({'msg':'下一次图形或规则保存将返回一次 503，用于验证保留编辑并重试。'})
    if kind == 'conflict':
        task.template_revision += 1
        db.session.commit()
        return jsonify({'msg': '已模拟其他窗口修改版本；下一次保存应提示冲突并保留本地编辑。'})
    region_type = 'line' if kind in ('cross', 'cross_reverse') else None
    regions = DeviceDetectionRegion.query.filter_by(task_id=1, device_id=device_id, is_enabled=True).order_by(DeviceDetectionRegion.id.desc()).all()
    region = next((r for r in regions if (r.region_type == 'line') == bool(region_type)), None)
    if region is None:
        return jsonify({'msg': '请先为选中摄像头画线或绘制区域并绑定规则'}), 400
    points = json.loads(region.points)
    track = int(time.time_ns() % 1_000_000_000) + 1
    if kind in ('cross', 'cross_reverse'):
        a, b = points[:2]
        mx, my = (a['x']+b['x'])/2, (a['y']+b['y'])/2
        dx, dy = b['x']-a['x'], b['y']-a['y']
        length = math.hypot(dx,dy) or 1
        positions = [(mx-dy/length*.12,my+dx/length*.12), (mx+dy/length*.12,my-dx/length*.12)]
        if kind == 'cross_reverse':
            positions.reverse()
    else:
        mx = sum(p['x'] for p in points)/len(points)
        my = sum(p['y'] for p in points)/len(points)
        positions = [(mx,my),(min(.99,max(p['x'] for p in points)+.1),my)] if kind == 'enter_exit' else [(mx,my),(mx,my)] if kind == 'dwell' else [(mx,my)]
    for index, (x,y) in enumerate(positions):
        count = 6 if kind == 'crowd' else 1
        dets = [{'model_id':1,'class_name':'person','class_id':0,'confidence':.95,'track_id':track+i,'bbox':[(x-.02)*1280,(y-.08)*720,(x+.02)*1280,y*720]} for i in range(count)]
        event = {'schema':'infer_event.v1','event_kind':'infer','correlation_id':str(uuid.uuid4()),'task_id':1,'task_type':'realtime','task_name':task.task_name,'device_id':device_id,'device_name':Device.query.get(device_id).name,'timestamp':(datetime.now(timezone.utc)+timedelta(seconds=index*2 if kind=='dwell' else 0)).isoformat(),'frame_width':1280,'frame_height':720,'model_ids':[1],'detections':dets}
        client.publish('mqtt/iot-infer-event',json.dumps(event),qos=1).wait_for_publish(timeout=3)
        time.sleep(.15)
    return jsonify({'msg':f'已通过真实 MQTT 发布 {len(positions)} 帧追踪测试输入；请刷新该图形统计。'})


@app.post('/video/regression/repush')
def repush():
    from app.services.post_template_client import put_template
    ok = put_template(1)
    return jsonify({'msg': ('已重新推送任务模板到 POST' if ok else '推送失败，请检查 POST 服务'), 'ok': bool(ok)})


@app.post('/video/regression/trainframe')
def trainframe():
    """Training-ground frame: publish one infer event from front-end driven actors.

    actors: [{track_id, x, y}] with normalized x/y in [0,1]; empty list = keepalive.
    """
    data = request.get_json() or {}
    device_id = data.get('device_id', 'regression-a')
    actors = data.get('actors') or []
    task = AlgorithmTask.query.get(1)
    device = Device.query.get(device_id)
    dets = []
    for a in actors:
        x, y = min(1, max(0, float(a['x']))), min(1, max(0, float(a['y'])))
        dets.append({'model_id':1,'class_name':'person','class_id':0,'confidence':.95,'track_id':int(a['track_id']),
                     'bbox':[(x-.02)*1280,(y-.08)*720,(x+.02)*1280,y*720]})
    event = {'schema':'infer_event.v1','event_kind':'infer','correlation_id':str(uuid.uuid4()),'task_id':1,'task_type':'realtime',
             'task_name':task.task_name,'device_id':device_id,'device_name':device.name if device else device_id,
             'timestamp':datetime.now(timezone.utc).isoformat(),'frame_width':1280,'frame_height':720,
             'model_ids':[1],'detections':dets}
    if not dets:
        event['hints'] = {'keepalive': True}
    client.publish('mqtt/iot-infer-event', json.dumps(event), qos=1).wait_for_publish(timeout=3)
    return jsonify({'msg': f'已发布 1 帧（{len(dets)} 个模拟目标）', 'published': len(dets)})


@app.route('/admin-api/<path:reference>', methods=['GET', 'POST'])
def reference_data(reference):
    # Ancillary Java-platform lookups only; geometry/bindings/results never use this.
    if 'model' in reference:
        return jsonify({'code':0,'data':{'list':[{'id':1,'name':'回归行人模型','model_name':'回归行人模型','model_type':'yolo','labels':['person']}],'total':1}})
    return jsonify({'code':0,'data':[],'total':0})


if __name__ == '__main__':
    with app.app_context():
        from app.services.post_template_client import put_template
        try:
            put_template(1)
        except Exception as exc:
            print('startup template push failed:', exc)
    client.connect('127.0.0.1',18883,60)
    client.loop_start()
    with app.app_context():
        from app.services.post_template_client import put_template
        put_template(1)
    print(f'ISOLATED regression DB: {WORK / "video.sqlite"}', flush=True)
    app.run(
        host=os.environ.get('MONITORING_REGRESSION_HOST', '127.0.0.1'),
        port=int(os.environ.get('MONITORING_REGRESSION_PORT', '6000')),
        threaded=True,
        use_reloader=False,
    )
