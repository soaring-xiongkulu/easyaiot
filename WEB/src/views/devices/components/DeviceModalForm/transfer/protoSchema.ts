export const defaultTelemetrySchema =
  'syntax ="proto3";\n' +
  'package telemetry;\n' +
  '\n' +
  'message SensorDataReading {\n' +
  '\n' +
  '  optional double temperature = 1;\n' +
  '  optional double humidity = 2;\n' +
  '  InnerObject innerObject = 3;\n' +
  '\n' +
  '  message InnerObject {\n' +
  '    optional string key1 = 1;\n' +
  '    optional bool key2 = 2;\n' +
  '    optional double key3 = 3;\n' +
  '    optional int32 key4 = 4;\n' +
  '    optional string key5 = 5;\n' +
  '  }\n' +
  '}\n';

export const defaultAttributesSchema =
  'syntax ="proto3";\n' +
  'package attributes;\n' +
  '\n' +
  'message SensorConfiguration {\n' +
  '  optional string firmwareVersion = 1;\n' +
  '  optional string serialNumber = 2;\n' +
  '}';

export const defaultRpcRequestSchema =
  'syntax ="proto3";\n' +
  'package rpc;\n' +
  '\n' +
  'message RpcRequestMsg {\n' +
  '  optional string method = 1;\n' +
  '  optional int32 requestId = 2;\n' +
  '  optional string params = 3;\n' +
  '}';

export const defaultRpcResponseSchema =
  'syntax ="proto3";\n' +
  'package rpc;\n' +
  '\n' +
  'message RpcResponseMsg {\n' +
  '  optional string payload = 1;\n' +
  '}';
