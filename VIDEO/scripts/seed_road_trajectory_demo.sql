-- 演示数据：沿深圳市福田区真实道路（金田路→红荔路）的 8 个摄像头 + 人脸/车牌匹配记录
-- 可重复执行（先清理旧演示数据）；清理方法见文件末尾注释
BEGIN;

DELETE FROM face_match_record  WHERE device_id LIKE 'demo-road-cam-%';
DELETE FROM plate_match_record WHERE device_id LIKE 'demo-road-cam-%';
DELETE FROM device             WHERE id LIKE 'demo-road-cam-%';

INSERT INTO device (id, name, source, rtmp_stream, http_stream, manufacturer, model, nvr_channel,
                    longitude, latitude, address, location_source, location_updated_at,
                    connection_status, auto_snap_enabled)
VALUES
('demo-road-cam-1','演示摄像头01','demo://demo-road-cam-1','rtmp://demo/live/demo-road-cam-1','http://demo/live/demo-road-cam-1.flv','演示','演示枪机',1,114.058220,22.543216,'深圳市福田区深南金田立交桥/金田路(1号杆)','manual',now(),'connect',false),
('demo-road-cam-2','演示摄像头02','demo://demo-road-cam-2','rtmp://demo/live/demo-road-cam-2','http://demo/live/demo-road-cam-2.flv','演示','演示枪机',2,114.058903,22.542154,'深圳市福田区金田路(2号杆)','manual',now(),'connect',false),
('demo-road-cam-3','演示摄像头03','demo://demo-road-cam-3','rtmp://demo/live/demo-road-cam-3','http://demo/live/demo-road-cam-3.flv','演示','演示枪机',3,114.065620,22.542724,'深圳市福田区金田路(3号杆)','manual',now(),'connect',false),
('demo-road-cam-4','演示摄像头04','demo://demo-road-cam-4','rtmp://demo/live/demo-road-cam-4','http://demo/live/demo-road-cam-4.flv','演示','演示枪机',4,114.068792,22.544714,'深圳市福田区金田路(4号杆)','manual',now(),'connect',false),
('demo-road-cam-5','演示摄像头05','demo://demo-road-cam-5','rtmp://demo/live/demo-road-cam-5','http://demo/live/demo-road-cam-5.flv','演示','演示枪机',5,114.068434,22.550939,'深圳市福田区红荔路(5号杆)','manual',now(),'connect',false),
('demo-road-cam-6','演示摄像头06','demo://demo-road-cam-6','rtmp://demo/live/demo-road-cam-6','http://demo/live/demo-road-cam-6.flv','演示','演示枪机',6,114.075213,22.551476,'深圳市福田区红荔路(6号杆)','manual',now(),'connect',false),
('demo-road-cam-7','演示摄像头07','demo://demo-road-cam-7','rtmp://demo/live/demo-road-cam-7','http://demo/live/demo-road-cam-7.flv','演示','演示枪机',7,114.079719,22.555771,'深圳市福田区红荔路(7号杆)','manual',now(),'connect',false),
('demo-road-cam-8','演示摄像头08','demo://demo-road-cam-8','rtmp://demo/live/demo-road-cam-8','http://demo/live/demo-road-cam-8.flv','演示','演示枪机',8,114.081580,22.559436,'深圳市福田区红荔路(8号杆)','manual',now(),'connect',false);

-- 人脸轨迹：张三，2026-08-31 上午（created_at 为 UTC，前端按东八区 09:xx–11:xx 展示）
-- cam-3 的第二条命中（01:44）距首条仅 8 分钟，用于演示同摄像头 15 分钟窗口合并逻辑
INSERT INTO face_match_record (device_id, device_name, matched, matched_person_name, similarity, threshold,
                               status, task_name, library_name, created_at)
VALUES
('demo-road-cam-1','演示摄像头01',true,'张三',0.93,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 01:03:00'),
('demo-road-cam-2','演示摄像头02',true,'张三',0.91,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 01:18:00'),
('demo-road-cam-3','演示摄像头03',true,'张三',0.96,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 01:36:00'),
('demo-road-cam-3','演示摄像头03',true,'张三',0.89,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 01:44:00'),
('demo-road-cam-4','演示摄像头04',true,'张三',0.88,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 01:52:00'),
('demo-road-cam-5','演示摄像头05',true,'张三',0.94,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 02:10:00'),
('demo-road-cam-6','演示摄像头06',true,'张三',0.9,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 02:25:00'),
('demo-road-cam-7','演示摄像头07',true,'张三',0.92,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 02:47:00'),
('demo-road-cam-8','演示摄像头08',true,'张三',0.87,0.80,'success','演示任务-道路轨迹','演示人脸库','2026-08-31 03:05:00');

-- 车牌轨迹：粤BD88888，同一条道路，时间与人物错开
INSERT INTO plate_match_record (device_id, device_name, plate_no, plate_color, matched, matched_owner_name,
                                detect_conf, status, task_name, library_name, created_at)
VALUES
('demo-road-cam-1','演示摄像头01','粤BD88888','蓝',true,'李四',0.96,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 01:10:00'),
('demo-road-cam-2','演示摄像头02','粤BD88888','蓝',true,'李四',0.94,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 01:31:00'),
('demo-road-cam-3','演示摄像头03','粤BD88888','蓝',true,'李四',0.97,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 01:49:00'),
('demo-road-cam-4','演示摄像头04','粤BD88888','蓝',true,'李四',0.9,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 02:06:00'),
('demo-road-cam-5','演示摄像头05','粤BD88888','蓝',true,'李四',0.93,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 02:21:00'),
('demo-road-cam-6','演示摄像头06','粤BD88888','蓝',true,'李四',0.95,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 02:40:00'),
('demo-road-cam-7','演示摄像头07','粤BD88888','蓝',true,'李四',0.92,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 02:58:00'),
('demo-road-cam-8','演示摄像头08','粤BD88888','蓝',true,'李四',0.89,'success','演示任务-道路轨迹','演示车牌库','2026-08-31 03:15:00');

COMMIT;

-- 清理演示数据：
--   DELETE FROM face_match_record  WHERE device_id LIKE 'demo-road-cam-%';
--   DELETE FROM plate_match_record WHERE device_id LIKE 'demo-road-cam-%';
--   DELETE FROM device             WHERE id LIKE 'demo-road-cam-%';
