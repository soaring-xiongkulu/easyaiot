-- EasyAIoT 工业协议演示种子（Modbus TCP / RTU / OPC UA）
-- 供 .scripts/industrial-demo/start_industrial_demo.sh 在 install/update 后写入/刷新。
-- 幂等：按固定 id UPSERT；随后脚本会把 host/endpoint/serialPort 改成当前可达地址。
-- 目标库：iot-device20

BEGIN;

-- 产品
INSERT INTO public.product (
  id, app_id, template_identification, product_name, product_identification,
  product_type, manufacturer_id, manufacturer_name, model, data_format,
  device_type, protocol_type, status, remark, create_by, create_time,
  update_by, update_time, auth_mode, user_name, password, connector,
  sign_key, encrypt_method, encrypt_key, encrypt_vector, tenant_id,
  public_key, private_key
) VALUES
  (910001, 'demo', NULL, 'Modbus TCP 演示产品', 'IND_MODBUS_TCP_DEMO',
   'COMMON', 'demo', 'EasyAIoT', 'modbus-tcp', 'BINARY',
   'COMMON', 'MODBUS_TCP', '0', 'industrial demo', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, NULL,
   NULL, 0, NULL, NULL, 1, NULL, NULL),
  (910002, 'demo', NULL, 'Modbus RTU 演示产品', 'IND_MODBUS_RTU_DEMO',
   'COMMON', 'demo', 'EasyAIoT', 'modbus-rtu', 'BINARY',
   'COMMON', 'MODBUS_RTU', '0', 'industrial demo', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, NULL,
   NULL, 0, NULL, NULL, 1, NULL, NULL),
  (910003, 'demo', NULL, 'OPC UA 演示产品', 'IND_OPCUA_DEMO',
   'COMMON', 'demo', 'EasyAIoT', 'opcua', 'BINARY',
   'COMMON', 'OPCUA', '0', 'industrial demo', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, NULL,
   NULL, 0, NULL, NULL, 1, NULL, NULL)
ON CONFLICT (id) DO UPDATE SET
  product_name = EXCLUDED.product_name,
  product_identification = EXCLUDED.product_identification,
  protocol_type = EXCLUDED.protocol_type,
  remark = EXCLUDED.remark,
  update_by = EXCLUDED.update_by,
  update_time = CURRENT_TIMESTAMP;

-- 物模型属性
INSERT INTO public.product_properties (
  id, property_name, property_code, datatype, description, enumlist,
  max, maxlength, method, min, required, step, unit, create_by, create_time,
  update_by, update_time, template_identification, product_identification, tenant_id
) VALUES
  (911001, '温度', 'temperature', 'DOUBLE', '演示温度', NULL, NULL, NULL, 'r', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_MODBUS_TCP_DEMO', 1),
  (911002, '设定值', 'setpoint', 'INT', '演示设定值', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_MODBUS_TCP_DEMO', 1),
  (911003, '运行', 'running', 'BOOL', '演示运行状态', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_MODBUS_TCP_DEMO', 1),
  (911011, '温度', 'temperature', 'DOUBLE', '演示温度', NULL, NULL, NULL, 'r', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_MODBUS_RTU_DEMO', 1),
  (911012, '设定值', 'setpoint', 'INT', '演示设定值', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_MODBUS_RTU_DEMO', 1),
  (911013, '运行', 'running', 'BOOL', '演示运行状态', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_MODBUS_RTU_DEMO', 1),
  (911021, '温度', 'temperature', 'DOUBLE', '演示温度', NULL, NULL, NULL, 'r', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_OPCUA_DEMO', 1),
  (911022, '设定值', 'setpoint', 'DOUBLE', '演示设定值', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_OPCUA_DEMO', 1),
  (911023, '运行', 'running', 'BOOL', '演示运行状态', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'IND_OPCUA_DEMO', 1)
ON CONFLICT (id) DO UPDATE SET
  property_name = EXCLUDED.property_name,
  property_code = EXCLUDED.property_code,
  datatype = EXCLUDED.datatype,
  description = EXCLUDED.description,
  method = EXCLUDED.method,
  product_identification = EXCLUDED.product_identification;

-- 演示设备（占位 host，启动脚本会改成当前可达地址）
INSERT INTO public.device (
  id, client_id, app_id, device_identification, device_name, device_description,
  device_status, connect_status, is_will, product_identification, create_by, create_time,
  update_by, update_time, remark, device_version, device_sn, ip_address, mac_address,
  active_status, extension, activated_time, last_online_time, parent_identification,
  device_type, tenant_id, deleted
) VALUES
  (920001, 'mtcp01', 'demo', 'DEV_MTCP_001', 'Modbus TCP 演示设备', 'industrial demo',
   'ENABLE', 'OFFLINE', NULL, 'IND_MODBUS_TCP_DEMO', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, 'SN_MTCP_001', '127.0.0.1', NULL,
   1,
   '{"protocolConfig":{"type":"MODBUS_TCP","enabled":true,"host":"127.0.0.1","port":5020,"unitId":1,"pollIntervalMs":5000,"points":[{"propertyCode":"temperature","identifier":"temperature","function":"HOLDING_REGISTER","address":0,"dataType":"UINT16","scale":0.1,"writable":false},{"propertyCode":"setpoint","identifier":"setpoint","function":"HOLDING_REGISTER","address":1,"dataType":"UINT16","scale":1,"writable":true},{"propertyCode":"running","identifier":"running","function":"COIL","address":0,"dataType":"UINT16","writable":true}]}}',
   CURRENT_TIMESTAMP, NULL, NULL, 'COMMON', 1, 0),
  (920002, 'mrtu01', 'demo', 'DEV_MRTU_001', 'Modbus RTU 演示设备', 'industrial demo',
   'ENABLE', 'OFFLINE', NULL, 'IND_MODBUS_RTU_DEMO', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, 'SN_MRTU_001', NULL, NULL,
   1,
   '{"protocolConfig":{"type":"MODBUS_RTU","enabled":true,"serialPort":"/tmp/easyaiot-modbus-rtu-u","baudRate":9600,"dataBits":8,"stopBits":"1","parity":"NONE","unitId":1,"transmitDelayMs":0,"pollIntervalMs":5000,"points":[{"propertyCode":"temperature","identifier":"temperature","function":"HOLDING_REGISTER","address":0,"dataType":"UINT16","scale":0.1,"writable":false},{"propertyCode":"setpoint","identifier":"setpoint","function":"HOLDING_REGISTER","address":1,"dataType":"UINT16","scale":1,"writable":true},{"propertyCode":"running","identifier":"running","function":"COIL","address":0,"dataType":"UINT16","writable":true}]}}',
   CURRENT_TIMESTAMP, NULL, NULL, 'COMMON', 1, 0),
  (920003, 'opcua01', 'demo', 'DEV_OPCUA_001', 'OPC UA 演示设备', 'industrial demo',
   'ENABLE', 'OFFLINE', NULL, 'IND_OPCUA_DEMO', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, 'SN_OPCUA_001', '127.0.0.1', NULL,
   1,
   '{"protocolConfig":{"type":"OPCUA","enabled":true,"endpointUrl":"opc.tcp://127.0.0.1:4840/freeopcua/server/","pollIntervalMs":5000,"points":[{"propertyCode":"temperature","identifier":"temperature","nodeId":"ns=2;s=Temperature","dataType":"FLOAT","writable":false},{"propertyCode":"setpoint","identifier":"setpoint","nodeId":"ns=2;s=Setpoint","dataType":"FLOAT","writable":true},{"propertyCode":"running","identifier":"running","nodeId":"ns=2;s=Running","dataType":"BOOLEAN","writable":true}]}}',
   CURRENT_TIMESTAMP, NULL, NULL, 'COMMON', 1, 0)
ON CONFLICT (id) DO UPDATE SET
  device_name = EXCLUDED.device_name,
  device_description = EXCLUDED.device_description,
  device_status = EXCLUDED.device_status,
  product_identification = EXCLUDED.product_identification,
  extension = EXCLUDED.extension,
  update_by = EXCLUDED.update_by,
  update_time = CURRENT_TIMESTAMP,
  deleted = 0;


-- ============================================================
-- 环境监测 / 智能安防演示种子（APP 面板新组件 demo：折线图/仪表盘/进度条/摄像头）
-- 对应模板：ENV_PANEL_DEMO（chart/gauge/status/text/button）、SEC_PANEL_DEMO（video/status/switch/button/progress/chart）
-- ============================================================

-- 产品
INSERT INTO public.product (
  id, app_id, template_identification, product_name, product_identification,
  product_type, manufacturer_id, manufacturer_name, model, data_format,
  device_type, protocol_type, status, remark, create_by, create_time,
  update_by, update_time, auth_mode, user_name, password, connector,
  sign_key, encrypt_method, encrypt_key, encrypt_vector, tenant_id,
  public_key, private_key
) VALUES
  (910004, 'demo', NULL, '智能安防演示产品', 'SECURITY_DEMO',
   'COMMON', 'demo', 'EasyAIoT', 'security-gw', 'JSON',
   'COMMON', 'GB28181', '0', '智能安防演示产品（摄像头/布防/警笛），演示 APP 面板摄像头组件', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, NULL,
   NULL, 0, NULL, NULL, 1, NULL, NULL),
  (910005, 'demo', NULL, '环境监测演示产品', 'ENV_MONITOR_DEMO',
   'COMMON', 'demo', 'EasyAIoT', 'env-station', 'JSON',
   'COMMON', 'MQTT', '0', '环境监测演示产品（温度/湿度/PM2.5/CO2），演示 APP 面板折线图与仪表盘组件', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, NULL,
   NULL, 0, NULL, NULL, 1, NULL, NULL)
ON CONFLICT (id) DO UPDATE SET
  product_name = EXCLUDED.product_name,
  product_identification = EXCLUDED.product_identification,
  protocol_type = EXCLUDED.protocol_type,
  remark = EXCLUDED.remark,
  update_by = EXCLUDED.update_by,
  update_time = CURRENT_TIMESTAMP;

-- 物模型属性（环境监测）
INSERT INTO public.product_properties (
  id, property_name, property_code, datatype, description, enumlist,
  max, maxlength, method, min, required, step, unit, create_by, create_time,
  update_by, update_time, template_identification, product_identification, tenant_id
) VALUES
  (911031, '温度', 'temperature', 'DOUBLE', '环境温度', NULL, 60, NULL, 'r', 0, 0, NULL, '℃', 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'ENV_MONITOR_DEMO', 1),
  (911032, '湿度', 'humidity', 'INT', '空气湿度', NULL, 100, NULL, 'r', 0, 0, NULL, '%', 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'ENV_MONITOR_DEMO', 1),
  (911033, 'PM2.5', 'pm25', 'INT', '细颗粒物浓度', NULL, 500, NULL, 'r', 0, 0, NULL, 'μg/m³', 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'ENV_MONITOR_DEMO', 1),
  (911034, '空气品质', 'air_quality', 'ENUM', '空气质量等级', '["优","良","轻度污染","中度污染"]', NULL, NULL, 'r', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'ENV_MONITOR_DEMO', 1),
  (911035, 'CO₂浓度', 'co2', 'INT', '二氧化碳浓度', NULL, 5000, NULL, 'r', 0, 0, NULL, 'ppm', 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'ENV_MONITOR_DEMO', 1)
ON CONFLICT (id) DO UPDATE SET
  property_name = EXCLUDED.property_name,
  property_code = EXCLUDED.property_code,
  datatype = EXCLUDED.datatype,
  description = EXCLUDED.description,
  enumlist = EXCLUDED.enumlist,
  method = EXCLUDED.method,
  product_identification = EXCLUDED.product_identification;

-- 物模型属性（智能安防）
INSERT INTO public.product_properties (
  id, property_name, property_code, datatype, description, enumlist,
  max, maxlength, method, min, required, step, unit, create_by, create_time,
  update_by, update_time, template_identification, product_identification, tenant_id
) VALUES
  (911041, '布防状态', 'arm_status', 'ENUM', '布防/撤防状态', '["armed","disarmed"]', NULL, NULL, 'r', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'SECURITY_DEMO', 1),
  (911042, '警笛', 'siren', 'BOOL', '警笛开关', NULL, NULL, NULL, 'w', NULL, 0, NULL, NULL, 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'SECURITY_DEMO', 1),
  (911043, '录像存储占用', 'storage', 'INT', '录像存储占用百分比', NULL, 100, NULL, 'r', 0, 0, NULL, '%', 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'SECURITY_DEMO', 1),
  (911044, '出入口客流', 'traffic', 'INT', '出入口实时客流', NULL, 50, NULL, 'r', 0, 0, NULL, '人', 'admin', CURRENT_TIMESTAMP, NULL, NULL, NULL, 'SECURITY_DEMO', 1)
ON CONFLICT (id) DO UPDATE SET
  property_name = EXCLUDED.property_name,
  property_code = EXCLUDED.property_code,
  datatype = EXCLUDED.datatype,
  description = EXCLUDED.description,
  enumlist = EXCLUDED.enumlist,
  method = EXCLUDED.method,
  product_identification = EXCLUDED.product_identification;

-- 演示设备（含 shadow，APP 面板组件可直接读取渲染）
INSERT INTO public.device (
  id, client_id, app_id, device_identification, device_name, device_description,
  device_status, connect_status, is_will, product_identification, create_by, create_time,
  update_by, update_time, remark, device_version, device_sn, ip_address, mac_address,
  active_status, extension, activated_time, last_online_time, parent_identification,
  device_type, tenant_id, deleted
) VALUES
  (920010, 'env01', 'demo', 'DEV_ENV_001', '环境监测站 A-01', 'env demo',
   'ENABLE', 'ONLINE', NULL, 'ENV_MONITOR_DEMO', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, '园区东门环境监测站', '1.0.0', 'SN_ENV_001', '192.168.1.31', NULL,
   1,
   '{"shadow": {"_raw": {"temperature": "26.5", "humidity": "58", "pm25": "32", "co2": "620"}, "temperature": 26.5, "humidity": 58, "pm25": 32, "air_quality": "良", "co2": 620}, "shadowUpdateTime": "2026-08-27T10:00:00+08:00"}',
   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, 'COMMON', 1, 0),
  (920011, 'sec01', 'demo', 'DEV_SEC_001', '安防网关 G-01', 'security demo',
   'ENABLE', 'ONLINE', NULL, 'SECURITY_DEMO', 'admin', CURRENT_TIMESTAMP,
   'admin', CURRENT_TIMESTAMP, '1 号楼智能安防网关', '1.0.0', 'SN_SEC_001', '192.168.1.32', NULL,
   1,
   '{"shadow": {"_raw": {"arm_status": "armed", "siren": "false", "storage": "46"}, "arm_status": "armed", "siren": false, "storage": 46, "traffic": 12}, "shadowUpdateTime": "2026-08-27T10:00:00+08:00"}',
   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, 'COMMON', 1, 0)
ON CONFLICT (id) DO UPDATE SET
  device_name = EXCLUDED.device_name,
  device_description = EXCLUDED.device_description,
  device_status = EXCLUDED.device_status,
  connect_status = EXCLUDED.connect_status,
  product_identification = EXCLUDED.product_identification,
  extension = EXCLUDED.extension,
  update_by = EXCLUDED.update_by,
  update_time = CURRENT_TIMESTAMP,
  deleted = 0;

COMMIT;
