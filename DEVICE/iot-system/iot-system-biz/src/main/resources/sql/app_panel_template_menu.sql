-- ============================================================
-- App 控制面板模板 —— WEB 管理端菜单脚本
-- 平台菜单为数据库驱动（permissionMode=BACK），部署时请执行本脚本，
-- 或在【系统管理 → 菜单管理】中手工添加等价菜单。
-- 说明：
--   * 组件路径 apppanel/index 对应 WEB/src/views/apppanel/index.vue
--   * 父级默认挂到「产品列表(device/product/index)」所在的同级目录下；
--     若找不到该父级则挂在根目录(parent_id=0)，可在菜单管理中调整。
--   * 执行后请在【系统管理 → 角色管理】为需要使用的角色分配该菜单。
-- ============================================================

INSERT INTO public.system_menu (
    id, name, permission, type, sort, parent_id, path, icon, component, component_name,
    status, visible, keep_alive, always_show, creator, updater
)
VALUES (
    9201, 'App面板模板', '', 2, 5,
    COALESCE((
        SELECT m.parent_id
        FROM public.system_menu m
        WHERE m.component = 'device/product/index' AND m.deleted = 0
        LIMIT 1
    ), 0),
    'app-panel-template', 'ant-design:appstore-outlined', 'apppanel/index', 'AppPanelTemplate',
    0, TRUE, TRUE, TRUE, '1', '1'
)
ON CONFLICT (id) DO NOTHING;
