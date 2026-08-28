-- ============================================================
-- FLOW 告警工单（原「工作流」）—— WEB 管理端菜单脚本
-- 执行库：ruoyi-vue-pro20（system 库）
-- 用法示例：
--   docker exec -i postgres-server psql -U postgres -d ruoyi-vue-pro20 < .scripts/flow/patches/flow_menu.sql
-- 说明：
--   * ID 段 3300-3399（当前库菜单最大 ID 为 3208，无冲突）；
--   * 组件路径 flow/xxx 对应 WEB/src/views/flow/xxx.vue（目录为 xxx/index.vue）；
--   * 模块已改名「告警工单」并去掉独立侧边栏菜单（顶级目录 visible=false），
--     入口收敛至【告警管理 → 告警工单 Tab】；保留全部菜单/按钮权限行（v-auth 依赖），
--     且路由仍会注册：流程设计页 /flow/model/design/:id、审批详情页
--     /flow/process-instance/detail（站内信/APP deepLink）跳转不受影响；
--   * 首次执行后请在【系统管理 → 角色管理】为需要使用的角色分配该菜单（按钮权限）。
-- ============================================================

BEGIN;

-- 目录：告警工单（原「工作流」，不再作为独立侧边栏菜单展示）
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3300, '告警工单', '', 1, 12, 0, '/flow', 'ant-design:apartment-outlined', NULL, NULL,
  0, false, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, path = EXCLUDED.path, icon = EXCLUDED.icon,
  sort = EXCLUDED.sort, visible = EXCLUDED.visible, update_time = NOW();

-- 菜单：流程模型（列表 + 新建 + 设计器入口 + 发布）
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3301, '流程模型', 'flow:model:query', 2, 1, 3300, 'model', 'ant-design:partition-outlined', 'flow/model/index', 'FlowModel',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 隐藏路由：流程设计器 /flow/model/design/:id
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3302, '流程设计', '', 2, 99, 3301, 'design/:id', '', 'flow/model/design', 'FlowModelDesign',
  0, false, false, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, path = EXCLUDED.path,
  component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  visible = EXCLUDED.visible, update_time = NOW();

-- 菜单：流程定义
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3303, '流程定义', 'flow:model:query', 2, 2, 3300, 'definition', 'ant-design:profile-outlined', 'flow/model/definition', 'FlowDefinition',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 目录：审批中心（同样不在侧边栏展示；待办/已办/抄送入口收敛至告警工单 Tab 内）
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3304, '审批中心', '', 1, 3, 3300, 'task', 'ant-design:audit-outlined', NULL, NULL,
  0, false, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, path = EXCLUDED.path,
  icon = EXCLUDED.icon, visible = EXCLUDED.visible, update_time = NOW();

-- 菜单：待办任务
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3305, '待办任务', 'flow:task:query', 2, 1, 3304, 'todo', 'ant-design:carry-out-outlined', 'flow/task/todo', 'FlowTaskTodo',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 菜单：已办任务
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3306, '已办任务', 'flow:task:query', 2, 2, 3304, 'done', 'ant-design:file-done-outlined', 'flow/task/done', 'FlowTaskDone',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 菜单：抄送我的
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3307, '抄送我的', 'flow:task:query', 2, 3, 3304, 'copy', 'ant-design:send-outlined', 'flow/task/copy', 'FlowTaskCopy',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 菜单：流程实例（Tabs：我的流程 / 全部流程）
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3308, '流程实例', 'flow:process-instance:query', 2, 4, 3300, 'process-instance', 'ant-design:node-index-outlined', 'flow/processInstance/index', 'FlowProcessInstance',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 隐藏路由：审批详情 /flow/process-instance/detail?id=&taskId=
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3309, '审批详情', '', 2, 99, 3308, 'detail', '', 'flow/processInstance/detail', 'FlowProcessInstanceDetail',
  0, false, false, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, parent_id = EXCLUDED.parent_id, path = EXCLUDED.path,
  component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  visible = EXCLUDED.visible, update_time = NOW();

-- 菜单：告警处理（Tabs：路由规则 / 处理记录）
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3310, '告警处理', 'flow:alert-route-rule:query', 2, 5, 3300, 'alert', 'ant-design:alert-outlined', 'flow/alert/index', 'FlowAlert',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 菜单：流程分类
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3311, '流程分类', 'flow:category:query', 2, 6, 3300, 'category', 'ant-design:tags-outlined', 'flow/category/index', 'FlowCategory',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 菜单：用户组
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES (
  3312, '用户组', 'flow:user-group:query', 2, 7, 3300, 'group', 'ant-design:team-outlined', 'flow/group/index', 'FlowUserGroup',
  0, true, true, true, '1', NOW(), '1', NOW(), 0
) ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  path = EXCLUDED.path, component = EXCLUDED.component, component_name = EXCLUDED.component_name,
  update_time = NOW();

-- 按钮权限：流程模型
INSERT INTO system_menu (
  id, name, permission, type, sort, parent_id, path, icon, component, component_name,
  status, visible, keep_alive, always_show, creator, create_time, updater, update_time, deleted
) VALUES
  (3321, '模型创建', 'flow:model:create', 3, 1, 3301, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3322, '模型更新', 'flow:model:update', 3, 2, 3301, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3323, '模型删除', 'flow:model:delete', 3, 3, 3301, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3324, '模型部署', 'flow:model:deploy', 3, 4, 3301, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  -- 按钮权限：流程分类
  (3325, '分类创建', 'flow:category:create', 3, 1, 3311, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3326, '分类更新', 'flow:category:update', 3, 2, 3311, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3327, '分类删除', 'flow:category:delete', 3, 3, 3311, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  -- 按钮权限：用户组
  (3328, '用户组创建', 'flow:user-group:create', 3, 1, 3312, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3329, '用户组更新', 'flow:user-group:update', 3, 2, 3312, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3330, '用户组删除', 'flow:user-group:delete', 3, 3, 3312, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  -- 按钮权限：告警路由规则 / 处理记录
  (3331, '规则创建', 'flow:alert-route-rule:create', 3, 1, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3332, '规则更新', 'flow:alert-route-rule:update', 3, 2, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3333, '规则删除', 'flow:alert-route-rule:delete', 3, 3, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3334, '规则启停', 'flow:alert-route-rule:enable', 3, 4, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3335, '规则试算', 'flow:alert-route-rule:preview', 3, 5, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3336, '记录查询', 'flow:alert-record:query', 3, 6, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3337, '记录手动触发', 'flow:alert-record:trigger', 3, 7, 3310, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  -- 按钮权限：流程实例 / 任务审批动作
  (3338, '实例撤销', 'flow:process-instance:cancel', 3, 1, 3308, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3339, '任务通过', 'flow:task:approve', 3, 10, 3305, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3340, '任务拒绝', 'flow:task:reject', 3, 11, 3305, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3341, '任务退回', 'flow:task:return', 3, 12, 3305, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3342, '任务委派', 'flow:task:delegate', 3, 13, 3305, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3343, '任务转办', 'flow:task:transfer', 3, 14, 3305, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0),
  (3344, '任务抄送', 'flow:task:copy', 3, 15, 3305, '', '', '', NULL, 0, true, true, true, '1', NOW(), '1', NOW(), 0)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, permission = EXCLUDED.permission, parent_id = EXCLUDED.parent_id,
  sort = EXCLUDED.sort, update_time = NOW();

COMMIT;
