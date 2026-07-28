-- TRANSFORM 系统对接菜单（WEB 动态路由 BACK 模式）
-- 执行库：ruoyi-vue-pro20（system 库）
-- 用法示例：
--   docker exec -i postgres-server psql -U postgres -d ruoyi-vue-pro20 < TRANSFORM/scripts/transform_menu.sql

BEGIN;

-- 非兼容模式：清理旧菜单及授权，按新结构重建
DELETE FROM system_role_menu WHERE menu_id BETWEEN 3200 AND 3208;
DELETE FROM system_menu WHERE id BETWEEN 3200 AND 3208;

INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3200, '数据转发', '', 2, 47, 0, '/transform', 'ant-design:send-outlined', 'transform/index', 'Transform',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  type = EXCLUDED.type,
  path = EXCLUDED.path,
  icon = EXCLUDED.icon,
  component = EXCLUDED.component,
  component_name = EXCLUDED.component_name,
  sort = EXCLUDED.sort,
  visible = EXCLUDED.visible,
  update_time = NOW();

INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES
  (3202, '对接概览查询', 'transform:overview:query', 3, 1, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3203, '目标系统查询', 'transform:party:query', 3, 2, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3204, '目标系统维护', 'transform:party:update', 3, 3, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3205, '推送规则查询', 'transform:contract:query', 3, 4, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3206, '推送规则维护', 'transform:contract:update', 3, 5, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3207, '推送记录再推', 'transform:outbox:replay', 3, 6, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3208, '失败记录再推', 'transform:dlq:replay', 3, 7, 3200, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  permission = EXCLUDED.permission,
  parent_id = 3200,
  update_time = NOW();

INSERT INTO system_role_menu (id, role_id, menu_id, creator, create_time, updater, update_time, deleted, tenant_id)
SELECT nextval('system_role_menu_seq'), 1, m.id, '1', NOW(), '1', NOW(), 0, 1
FROM system_menu m
WHERE m.id BETWEEN 3200 AND 3208
  AND NOT EXISTS (
    SELECT 1 FROM system_role_menu rm WHERE rm.role_id = 1 AND rm.menu_id = m.id AND rm.deleted = 0
  );

COMMIT;
