-- 删除推流转发任务表中的 run_status 字段
-- 只根据 is_enabled 来判断任务状态：
--   is_enabled=True: 运行中
--   is_enabled=False: 已停止
-- 适用于PostgreSQL数据库

ALTER TABLE stream_forward_task 
DROP COLUMN IF EXISTS run_status;

COMMENT ON TABLE stream_forward_task IS '推流转发任务表（用于批量推送多个摄像头实时画面，无需AI）。任务状态只根据 is_enabled 判断：True=运行中，False=已停止';
