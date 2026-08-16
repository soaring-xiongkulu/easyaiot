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

COMMIT;
