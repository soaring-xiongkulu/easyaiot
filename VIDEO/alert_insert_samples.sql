-- 告警记录INSERT语句示例（10条）

-- 1. 人员入侵告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('person', 'intrusion', 'A区', '检测到未授权人员进入A区，置信度: 0.95', 'CAM001', '前门摄像头', '/data/images/alert_001.jpg', '/data/records/alert_001.mp4');

-- 2. 车辆违停告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('vehicle', 'illegal_parking', '停车场B区', '检测到车辆在禁停区域停留超过5分钟', 'CAM002', '停车场摄像头', '/data/images/alert_002.jpg', '/data/records/alert_002.mp4');

-- 3. 火灾检测告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('fire', 'fire_detection', '仓库C区', '检测到疑似火源，温度异常升高', 'CAM003', '仓库监控', '/data/images/alert_003.jpg', '/data/records/alert_003.mp4');

-- 4. 人员聚集告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('person', 'crowd_gathering', '大厅', '检测到人员异常聚集，人数超过10人', 'CAM004', '大厅摄像头', '/data/images/alert_004.jpg', '/data/records/alert_004.mp4');

-- 5. 物品遗留告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('bag', 'abandoned_object', '安检区', '检测到可疑物品遗留，超过30分钟未移动', 'CAM005', '安检摄像头', '/data/images/alert_005.jpg', '/data/records/alert_005.mp4');

-- 6. 人员徘徊告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('person', 'loitering', 'D区通道', '检测到人员在敏感区域徘徊超过10分钟', 'CAM006', '通道监控', '/data/images/alert_006.jpg', '/data/records/alert_006.mp4');

-- 7. 车辆超速告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('vehicle', 'overspeed', '主干道', '检测到车辆超速行驶，速度: 85km/h，限速: 60km/h', 'CAM007', '道路监控', '/data/images/alert_007.jpg', '/data/records/alert_007.mp4');

-- 8. 异常行为告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('person', 'abnormal_behavior', 'E区', '检测到异常行为：快速移动并翻越围栏', 'CAM008', '周界监控', '/data/images/alert_008.jpg', '/data/records/alert_008.mp4');

-- 9. 烟雾检测告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('smoke', 'smoke_detection', '机房', '检测到烟雾，可能发生火灾或设备故障', 'CAM009', '机房监控', '/data/images/alert_009.jpg', '/data/records/alert_009.mp4');

-- 10. 人员摔倒告警
INSERT INTO public.alert (object, event, region, information, device_id, device_name, image_path, record_path)
VALUES ('person', 'fall_detection', 'F区走廊', '检测到人员摔倒，可能需要医疗救助', 'CAM010', '走廊监控', '/data/images/alert_010.jpg', '/data/records/alert_010.mp4');

