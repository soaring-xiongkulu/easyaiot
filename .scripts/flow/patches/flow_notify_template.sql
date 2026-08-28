-- FLOW 站内信模板：待办提醒（含 deepLink，APP/PC 消息中心解析 flow://instance/{id}?taskId={taskId} 跳转审批详情）
-- 目标库：ruoyi-vue-pro20
INSERT INTO system_notify_template (id, name, code, nickname, content, type, params, status, remark, creator, updater, deleted, create_time, update_time)
VALUES (1001, '流程待办提醒', 'flow_task_todo', '告警工单',
        '您有一条新的审批待办：{processInstanceName}，当前节点「{taskName}」，发起人：{startUser}。请及时处理：{deepLink}',
        2, '["processInstanceName","taskName","startUser","deepLink"]', 0, '告警工单待办提醒', '1', '1', 0, NOW(), NOW())
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name, code = EXCLUDED.code, nickname = EXCLUDED.nickname, content = EXCLUDED.content,
    type = EXCLUDED.type, params = EXCLUDED.params, status = EXCLUDED.status, remark = EXCLUDED.remark,
    updater = EXCLUDED.updater, deleted = 0, update_time = NOW();
