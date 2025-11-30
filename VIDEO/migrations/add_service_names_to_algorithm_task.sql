-- 为算法任务表添加service_names字段
-- 用于存储关联的算法服务名称列表（逗号分隔），避免跨模块查询
-- 适用于PostgreSQL数据库

ALTER TABLE algorithm_task 
ADD COLUMN service_names TEXT;

COMMENT ON COLUMN algorithm_task.service_names IS '关联的算法服务名称列表（逗号分隔，用于快速显示）';

-- 更新现有数据：从algorithm_model_service表中提取服务名称
UPDATE algorithm_task at
SET service_names = (
    SELECT string_agg(ams.service_name, ', ' ORDER BY ams.sort_order, ams.id)
    FROM algorithm_model_service ams
    WHERE ams.task_id = at.id
)
WHERE EXISTS (
    SELECT 1 FROM algorithm_model_service ams WHERE ams.task_id = at.id
);

