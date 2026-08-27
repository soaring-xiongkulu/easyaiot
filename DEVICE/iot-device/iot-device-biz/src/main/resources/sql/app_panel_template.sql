-- App 控制面板模板表：云端定制每个产品在 APP 内展示的控制页面，绑定产品后下发到 APP 动态渲染
-- 注意：panel_schema 存储模板 JSON（页面 + 组件配置），App 端按该 JSON 动态渲染控制页

CREATE TABLE IF NOT EXISTS public.app_panel_template (
    id BIGSERIAL NOT NULL,
    template_code VARCHAR(64) NOT NULL, -- 模板编码：全局唯一，App 可按编码兜底取默认模板
    template_name VARCHAR(128) NOT NULL, -- 模板名称
    product_identification VARCHAR(100), -- 绑定产品标识（对应 product.product_identification）
    status VARCHAR(16) DEFAULT 'DRAFT' NOT NULL, -- 状态：DRAFT-草稿，PUBLISHED-已发布，DISABLED-停用
    version INT DEFAULT 1, -- 版本号，每次发布自增
    panel_schema TEXT, -- 面板模板 JSON：pages[{name,widgets[{id,type,title,...}]}]
    remark VARCHAR(255) NULL, -- 备注
    created_by VARCHAR(64) NULL,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL,
    updated_by VARCHAR(64) NULL,
    updated_time TIMESTAMP NULL,
    tenant_id BIGINT DEFAULT 0 NOT NULL,
    deleted INT DEFAULT 0 NOT NULL,
    CONSTRAINT app_panel_template_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_app_panel_template_code ON public.app_panel_template(template_code);
CREATE INDEX IF NOT EXISTS idx_app_panel_template_product_identification ON public.app_panel_template(product_identification);
CREATE INDEX IF NOT EXISTS idx_app_panel_template_tenant_id ON public.app_panel_template(tenant_id);

COMMENT ON TABLE public.app_panel_template IS 'App控制面板模板表';
COMMENT ON COLUMN public.app_panel_template.id IS '主键';
COMMENT ON COLUMN public.app_panel_template.template_code IS '模板编码：全局唯一';
COMMENT ON COLUMN public.app_panel_template.template_name IS '模板名称';
COMMENT ON COLUMN public.app_panel_template.product_identification IS '绑定产品标识';
COMMENT ON COLUMN public.app_panel_template.status IS '状态：DRAFT-草稿，PUBLISHED-已发布，DISABLED-停用';
COMMENT ON COLUMN public.app_panel_template.version IS '版本号，每次发布自增';
COMMENT ON COLUMN public.app_panel_template.panel_schema IS '面板模板JSON：pages[{name,widgets[...]}]';
COMMENT ON COLUMN public.app_panel_template.remark IS '备注';
COMMENT ON COLUMN public.app_panel_template.tenant_id IS '租户编号';
COMMENT ON COLUMN public.app_panel_template.deleted IS '是否删除：0-未删除，1-已删除';


-- ============================================================
-- 演示面板模板数据（5 个，幂等 UPSERT）
-- 说明：iot-device10.sql 中同步自本文件，修改后需同步更新
-- ============================================================
INSERT INTO public.app_panel_template (
  id, template_code, template_name, product_identification, status, version,
  panel_schema, remark, created_by, created_time, updated_by, updated_time,
  tenant_id, deleted
) VALUES
  (1, 'PLUG_PANEL_DEMO', '智能插座控制面板（演示）', 'IND_MODBUS_TCP_DEMO', 'PUBLISHED', 2,
   '{"version": 1, "pages": [{"name": "控制台", "layout": "grid", "widgets": [{"id": "power_switch", "type": "switch", "title": "电源开关", "span": "half", "propertyCode": "power", "config": {"options": [{"label": "开启", "value": "1", "color": "#2f6bff"}, {"label": "关闭", "value": "0", "color": "#8c8c8c"}]}}, {"id": "work_status", "type": "status", "title": "工作状态", "span": "half", "propertyCode": "work_status", "config": {"options": [{"label": "运行", "value": "RUNNING", "color": "#16c2a2"}, {"label": "待机", "value": "STANDBY", "color": "#8c8c8c"}, {"label": "故障", "value": "FAULT", "color": "#f5222d"}]}}, {"id": "power_consumption", "type": "text", "title": "实时功率", "span": "half", "propertyCode": "power_consumption", "config": {"unit": "W"}}, {"id": "threshold", "type": "slider", "title": "定时电量阈值", "span": "half", "propertyCode": "threshold", "config": {"min": 0, "max": 100, "step": 5, "unit": "%"}}, {"id": "reboot", "type": "button", "title": "重启设备", "span": "full", "serviceId": "reboot", "config": {"confirm": true}}]}]}',
   '演示模板：电源开关/工作状态/实时功率/电量阈值/重启', NULL, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, 1, 0),
  (2, 'RTU_TEMP_PANEL', 'Modbus RTU 温控面板（演示）', 'IND_MODBUS_RTU_DEMO', 'PUBLISHED', 2,
   '{"version": 1, "pages": [{"name": "控制台", "layout": "grid", "widgets": [{"id": "running", "type": "switch", "title": "运行开关", "span": "half", "propertyCode": "running", "config": {"options": [{"label": "开启", "value": "true", "color": "#2f6bff"}, {"label": "关闭", "value": "false", "color": "#8c8c8c"}]}}, {"id": "temperature", "type": "text", "title": "温度", "span": "half", "propertyCode": "temperature", "config": {"unit": "℃"}}, {"id": "setpoint", "type": "slider", "title": "设定值", "span": "half", "propertyCode": "setpoint", "config": {"min": 0, "max": 100, "step": 1, "unit": ""}}, {"id": "refresh", "type": "button", "title": "重启设备", "span": "full", "serviceId": "restart", "config": {"confirm": true}}]}]}',
   '绑定设备 DEV_MRTU_001（920002，ONLINE），属性与 shadow 对应', NULL, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, 1, 0),
  (3, 'ESS_PANEL', '储能设备控制面板（演示）', '9820630576939008', 'PUBLISHED', 2,
   '{"version": 1, "pages": [{"name": "控制台", "layout": "grid", "widgets": [{"id": "vbat", "type": "text", "title": "电池电量", "span": "half", "propertyCode": "Vbatt", "config": {"unit": "V"}}, {"id": "angx", "type": "status", "title": "X轴倾角", "span": "half", "propertyCode": "PVAngle_X", "config": {"options": [{"label": "正常", "value": "4.96", "color": "#16c2a2"}, {"label": "倾斜", "value": "45", "color": "#f5222d"}]}}, {"id": "angy", "type": "text", "title": "Y轴倾角", "span": "half", "propertyCode": "PVAngle_Y", "config": {"unit": "°"}}, {"id": "svc", "type": "button", "title": "触发服务", "span": "full", "serviceId": "demo-svc", "config": {"confirm": false}}]}]}',
   '绑定设备 9720084293632004（57038，ONLINE）', NULL, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, 1, 0),
  (4, 'ENV_PANEL_DEMO', '环境监测面板（演示）', 'ENV_MONITOR_DEMO', 'PUBLISHED', 2,
   '{"version": 1, "pages": [{"name": "环境监测", "layout": "grid", "widgets": [{"id": "temp", "type": "chart", "title": "温度趋势", "span": "full", "propertyCode": "temperature", "config": {"min": 0, "max": 60, "unit": "℃", "color": "#2f6bff", "maxPoints": 20}}, {"id": "humi", "type": "gauge", "title": "空气湿度", "span": "half", "propertyCode": "humidity", "config": {"min": 0, "max": 100, "unit": "%", "color": "#16c2a2"}}, {"id": "pm25", "type": "gauge", "title": "PM2.5", "span": "half", "propertyCode": "pm25", "config": {"min": 0, "max": 500, "unit": "μg/m³", "color": "#f5a623"}}, {"id": "airq", "type": "status", "title": "空气品质", "span": "half", "propertyCode": "air_quality", "config": {"options": [{"label": "优", "value": "优", "color": "#16c2a2"}, {"label": "良", "value": "良", "color": "#2f6bff"}, {"label": "轻度污染", "value": "轻度污染", "color": "#f5a623"}, {"label": "中度污染", "value": "中度污染", "color": "#f5222d"}]}}, {"id": "co2", "type": "text", "title": "CO₂ 浓度", "span": "half", "propertyCode": "co2", "config": {"unit": "ppm"}}, {"id": "inspect", "type": "button", "title": "触发设备巡检", "span": "full", "serviceId": "inspect", "config": {"confirm": true}}]}]}',
   NULL, NULL, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, 1, 0),
  (5, 'SEC_PANEL_DEMO', '智能安防面板（演示）', 'SECURITY_DEMO', 'PUBLISHED', 2,
   '{"version": 1, "pages": [{"name": "安防控制台", "layout": "grid", "widgets": [{"id": "cam", "type": "video", "title": "实时画面", "span": "full"}, {"id": "arm", "type": "status", "title": "布防状态", "span": "half", "propertyCode": "arm_status", "config": {"options": [{"label": "已布防", "value": "armed", "color": "#16c2a2"}, {"label": "已撤防", "value": "disarmed", "color": "#f5a623"}]}}, {"id": "siren", "type": "switch", "title": "警笛开关", "span": "half", "propertyCode": "siren"}, {"id": "armbtn", "type": "button", "title": "一键布防", "span": "half", "serviceId": "arm", "config": {"confirm": true}}, {"id": "snap", "type": "button", "title": "一键抓拍", "span": "half", "serviceId": "snapshot"}, {"id": "stor", "type": "progress", "title": "录像存储占用", "span": "full", "propertyCode": "storage", "config": {"min": 0, "max": 100, "unit": "%"}}, {"id": "flow", "type": "chart", "title": "出入口客流", "span": "full", "propertyCode": "traffic", "config": {"min": 0, "max": 50, "unit": "人", "color": "#7b61ff", "maxPoints": 20}}]}]}',
   NULL, NULL, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, 1, 0)
ON CONFLICT (id) DO UPDATE SET
  template_code = EXCLUDED.template_code,
  template_name = EXCLUDED.template_name,
  product_identification = EXCLUDED.product_identification,
  status = EXCLUDED.status,
  version = EXCLUDED.version,
  panel_schema = EXCLUDED.panel_schema,
  remark = EXCLUDED.remark,
  updated_time = CURRENT_TIMESTAMP,
  deleted = 0;

-- 模板 id 固定，插入后同步序列，避免后续自增冲突
SELECT setval('app_panel_template_id_seq', (SELECT MAX(id) FROM public.app_panel_template));
