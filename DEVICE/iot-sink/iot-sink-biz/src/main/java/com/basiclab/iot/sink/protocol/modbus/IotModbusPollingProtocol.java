package com.basiclab.iot.sink.protocol.modbus;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import com.basiclab.iot.sink.dal.mapper.DeviceMapper;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.protocol.polling.AbstractIndustrialPollingProtocol;
import com.basiclab.iot.sink.protocol.polling.IndustrialDeviceConfig;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import com.digitalpetri.modbus.client.ModbusTcpClient;
import com.digitalpetri.modbus.pdu.ReadCoilsRequest;
import com.digitalpetri.modbus.pdu.ReadCoilsResponse;
import com.digitalpetri.modbus.pdu.ReadDiscreteInputsRequest;
import com.digitalpetri.modbus.pdu.ReadDiscreteInputsResponse;
import com.digitalpetri.modbus.pdu.ReadHoldingRegistersRequest;
import com.digitalpetri.modbus.pdu.ReadHoldingRegistersResponse;
import com.digitalpetri.modbus.pdu.ReadInputRegistersRequest;
import com.digitalpetri.modbus.pdu.ReadInputRegistersResponse;
import com.digitalpetri.modbus.pdu.WriteSingleCoilRequest;
import com.digitalpetri.modbus.pdu.WriteSingleRegisterRequest;
import com.digitalpetri.modbus.pdu.WriteMultipleRegistersRequest;
import com.digitalpetri.modbus.tcp.client.NettyClientTransportConfig;
import com.digitalpetri.modbus.tcp.client.NettyTcpClientTransport;
import lombok.extern.slf4j.Slf4j;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
public class IotModbusPollingProtocol extends AbstractIndustrialPollingProtocol {

    public static final String PROTOCOL_TYPE = "MODBUS_TCP";

    private final Map<String, ModbusTcpClient> clients = new ConcurrentHashMap<>();
    private final Map<String, Object> clientLocks = new ConcurrentHashMap<>();

    public IotModbusPollingProtocol(IotGatewayProperties.PollingProtocolProperties properties,
                                    DeviceMapper deviceMapper,
                                    IotDeviceMessageService messageService,
                                    IotMessageBus messageBus,
                                    DeviceServerIdService deviceServerIdService,
                                    String serverId) {
        super(PROTOCOL_TYPE, serverId, properties, deviceMapper, messageService, messageBus, deviceServerIdService);
    }

    @Override
    protected Map<String, Object> poll(DeviceDO device, IndustrialDeviceConfig config) throws Exception {
        String host = StrUtil.blankToDefault(config.getHost(), device.getIpAddress());
        if (StrUtil.isBlank(host)) {
            throw new IllegalArgumentException("Modbus TCP host is missing");
        }
        int port = config.getPort() == null ? 502 : config.getPort();
        int unitId = config.getUnitId() == null ? 1 : config.getUnitId();
        String key = clientKey(host, port);
        Object lock = clientLocks.computeIfAbsent(key, ignored -> new Object());
        synchronized (lock) {
            ModbusTcpClient client = acquireClientLocked(host, port, key);
            Map<String, Object> values = new LinkedHashMap<>();
            Map<String, String> rawValues = new LinkedHashMap<>();
            for (IndustrialDeviceConfig.Point point : config.getPoints()) {
                if (point == null || !point.hasResolvedPropertyCode() || point.getAddress() == null) {
                    continue;
                }
                String propertyCode = point.resolvedPropertyCode();
                PointReadResult result = readPoint(client, unitId, point);
                values.put(propertyCode, result.value());
                rawValues.put(propertyCode, result.rawPayload());
            }
            if (!rawValues.isEmpty()) {
                values.put("_raw", rawValues);
            }
            return values;
        }
    }

    @Override
    protected void write(DeviceDO device, IndustrialDeviceConfig config, IotDeviceMessage message) throws Exception {
        String host = StrUtil.blankToDefault(config.getHost(), device.getIpAddress());
        if (StrUtil.isBlank(host)) {
            throw new IllegalArgumentException("Modbus TCP host is missing");
        }
        int port = config.getPort() == null ? 502 : config.getPort();
        int unitId = config.getUnitId() == null ? 1 : config.getUnitId();
        String key = clientKey(host, port);
        Object lock = clientLocks.computeIfAbsent(key, ignored -> new Object());
        synchronized (lock) {
            ModbusTcpClient client = acquireClientLocked(host, port, key);
            for (IndustrialDeviceConfig.Point point : config.getPoints()) {
                if (point == null || !Boolean.TRUE.equals(point.getWritable()) || point.getAddress() == null
                        || !point.hasResolvedPropertyCode()) {
                    continue;
                }
                Object value = IotDeviceMessageUtils.extractPropertyValue(message, point.resolvedPropertyCode());
                if (value == null) {
                    continue;
                }
                if ("COIL".equalsIgnoreCase(point.getFunction())) {
                    boolean booleanValue = value instanceof Boolean bool ? bool : Boolean.parseBoolean(String.valueOf(value));
                    client.writeSingleCoil(unitId, new WriteSingleCoilRequest(point.getAddress(), booleanValue));
                } else if (value instanceof Number number) {
                    byte[] registerBytes = encodeRegisters(number, point);
                    if (registerBytes.length == 2) {
                        int rawValue = ByteBuffer.wrap(registerBytes).order(ByteOrder.BIG_ENDIAN).getShort() & 0xffff;
                        client.writeSingleRegister(unitId, new WriteSingleRegisterRequest(point.getAddress(), rawValue));
                    } else {
                        client.writeMultipleRegisters(unitId, new WriteMultipleRegistersRequest(
                                point.getAddress(), registerBytes.length / 2, registerBytes));
                    }
                }
            }
        }
    }

    private ModbusTcpClient acquireClientLocked(String host, int port, String key) throws Exception {
        ModbusTcpClient existing = clients.get(key);
        if (existing != null && existing.isConnected()) {
            return existing;
        }
        if (existing != null) {
            disconnectQuietly(existing);
            clients.remove(key, existing);
        }
        ModbusTcpClient client = createClient(host, port);
        client.connect();
        clients.put(key, client);
        return client;
    }

    private ModbusTcpClient createClient(String host, int port) {
        NettyClientTransportConfig transportConfig = NettyClientTransportConfig.create(builder -> {
            builder.hostname = host;
            builder.port = port;
            builder.connectTimeout = Duration.ofMillis(requestTimeoutMs());
            builder.connectPersistent = true;
        });
        return ModbusTcpClient.create(new NettyTcpClientTransport(transportConfig),
                builder -> builder.requestTimeout = Duration.ofMillis(requestTimeoutMs()));
    }

    @Override
    protected void invalidateConnection(DeviceDO device, IndustrialDeviceConfig config) {
        String host = StrUtil.blankToDefault(config.getHost(), device.getIpAddress());
        if (StrUtil.isBlank(host)) {
            return;
        }
        int port = config.getPort() == null ? 502 : config.getPort();
        String key = clientKey(host, port);
        Object lock = clientLocks.computeIfAbsent(key, ignored -> new Object());
        synchronized (lock) {
            ModbusTcpClient client = clients.remove(key);
            disconnectQuietly(client);
        }
    }

    @Override
    protected void closeConnections() {
        for (Map.Entry<String, ModbusTcpClient> entry : clients.entrySet()) {
            disconnectQuietly(entry.getValue());
        }
        clients.clear();
    }

    private static void disconnectQuietly(ModbusTcpClient client) {
        if (client == null) {
            return;
        }
        try {
            client.disconnect();
        } catch (Exception e) {
            log.debug("[disconnectQuietly][modbus tcp disconnect failed]", e);
        }
    }

    private static String clientKey(String host, int port) {
        return host + ":" + port;
    }

    private PointReadResult readPoint(ModbusTcpClient client, int unitId,
                                      IndustrialDeviceConfig.Point point) throws Exception {
        String function = StrUtil.blankToDefault(point.getFunction(), "HOLDING_REGISTER").toUpperCase();
        int configuredQuantity = point.getQuantity() == null ? 1 : point.getQuantity();
        int quantity = Math.max(defaultQuantity(point.getDataType()), configuredQuantity);
        return switch (function) {
            case "COIL" -> {
                ReadCoilsResponse response = client.readCoils(unitId,
                        new ReadCoilsRequest(point.getAddress(), quantity));
                byte[] raw = response.coils();
                yield new PointReadResult((raw[0] & 0x01) == 1, formatResponsePdu(unitId, 0x01, raw));
            }
            case "DISCRETE_INPUT" -> {
                ReadDiscreteInputsResponse response = client.readDiscreteInputs(unitId,
                        new ReadDiscreteInputsRequest(point.getAddress(), quantity));
                byte[] raw = response.inputs();
                yield new PointReadResult((raw[0] & 0x01) == 1, formatResponsePdu(unitId, 0x02, raw));
            }
            case "INPUT_REGISTER" -> {
                ReadInputRegistersResponse response = client.readInputRegisters(unitId,
                        new ReadInputRegistersRequest(point.getAddress(), quantity));
                byte[] raw = response.registers();
                yield new PointReadResult(decodeRegisters(raw, point), formatResponsePdu(unitId, 0x04, raw));
            }
            case "HOLDING_REGISTER" -> {
                ReadHoldingRegistersResponse response = client.readHoldingRegisters(unitId,
                        new ReadHoldingRegistersRequest(point.getAddress(), quantity));
                byte[] raw = response.registers();
                yield new PointReadResult(decodeRegisters(raw, point), formatResponsePdu(unitId, 0x03, raw));
            }
            default -> throw new IllegalArgumentException("Unsupported Modbus function: " + function);
        };
    }

    record PointReadResult(Object value, String rawPayload) {
    }

    static String formatResponsePdu(int unitId, int functionCode, byte[] data) {
        StringBuilder result = new StringBuilder();
        appendHexByte(result, unitId);
        appendHexByte(result, functionCode);
        appendHexByte(result, data.length);
        for (byte value : data) {
            appendHexByte(result, value & 0xff);
        }
        return result.toString();
    }

    private static void appendHexByte(StringBuilder target, int value) {
        if (!target.isEmpty()) {
            target.append(' ');
        }
        target.append(String.format("%02X", value & 0xff));
    }

    static Object decodeRegisters(byte[] source, IndustrialDeviceConfig.Point point) {
        if (source == null || source.length < 2) {
            throw new IllegalArgumentException("Modbus register response is empty");
        }
        byte[] bytes = source.clone();
        if ("LITTLE_ENDIAN".equalsIgnoreCase(point.getByteOrder())) {
            for (int index = 0; index + 1 < bytes.length; index += 2) {
                byte value = bytes[index];
                bytes[index] = bytes[index + 1];
                bytes[index + 1] = value;
            }
        }
        if ("LITTLE_ENDIAN".equalsIgnoreCase(point.getWordOrder()) && bytes.length > 2) {
            for (int left = 0, right = bytes.length - 2; left < right; left += 2, right -= 2) {
                byte first = bytes[left];
                byte second = bytes[left + 1];
                bytes[left] = bytes[right];
                bytes[left + 1] = bytes[right + 1];
                bytes[right] = first;
                bytes[right + 1] = second;
            }
        }

        ByteBuffer buffer = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN);
        String dataType = StrUtil.blankToDefault(point.getDataType(), "UINT16").toUpperCase();
        Number raw = switch (dataType) {
            case "INT16" -> buffer.getShort();
            case "UINT16" -> buffer.getShort() & 0xffff;
            case "INT32" -> buffer.getInt();
            case "UINT32" -> Integer.toUnsignedLong(buffer.getInt());
            case "FLOAT32" -> buffer.getFloat();
            case "INT64" -> buffer.getLong();
            case "FLOAT64" -> buffer.getDouble();
            default -> throw new IllegalArgumentException("Unsupported Modbus data type: " + dataType);
        };
        double scale = point.getScale() == null ? 1D : point.getScale();
        double offset = point.getOffset() == null ? 0D : point.getOffset();
        if (scale == 1D && offset == 0D && !dataType.startsWith("FLOAT")) {
            return raw;
        }
        return raw.doubleValue() * scale + offset;
    }

    static byte[] encodeRegisters(Number value, IndustrialDeviceConfig.Point point) {
        double scale = point.getScale() == null || point.getScale() == 0D ? 1D : point.getScale();
        double offset = point.getOffset() == null ? 0D : point.getOffset();
        double raw = (value.doubleValue() - offset) / scale;
        String dataType = StrUtil.blankToDefault(point.getDataType(), "UINT16").toUpperCase();
        ByteBuffer buffer = switch (dataType) {
            case "INT16", "UINT16" -> ByteBuffer.allocate(2).putShort((short) Math.round(raw));
            case "INT32", "UINT32" -> ByteBuffer.allocate(4).putInt((int) Math.round(raw));
            case "FLOAT32" -> ByteBuffer.allocate(4).putFloat((float) raw);
            case "INT64" -> ByteBuffer.allocate(8).putLong(Math.round(raw));
            case "FLOAT64" -> ByteBuffer.allocate(8).putDouble(raw);
            default -> throw new IllegalArgumentException("Unsupported Modbus data type: " + dataType);
        };
        byte[] bytes = buffer.array();
        if ("LITTLE_ENDIAN".equalsIgnoreCase(point.getWordOrder()) && bytes.length > 2) {
            for (int left = 0, right = bytes.length - 2; left < right; left += 2, right -= 2) {
                byte first = bytes[left];
                byte second = bytes[left + 1];
                bytes[left] = bytes[right];
                bytes[left + 1] = bytes[right + 1];
                bytes[right] = first;
                bytes[right + 1] = second;
            }
        }
        if ("LITTLE_ENDIAN".equalsIgnoreCase(point.getByteOrder())) {
            for (int index = 0; index + 1 < bytes.length; index += 2) {
                byte first = bytes[index];
                bytes[index] = bytes[index + 1];
                bytes[index + 1] = first;
            }
        }
        return bytes;
    }

    private int defaultQuantity(String dataType) {
        String type = StrUtil.blankToDefault(dataType, "UINT16").toUpperCase();
        return switch (type) {
            case "INT32", "UINT32", "FLOAT32" -> 2;
            case "INT64", "FLOAT64" -> 4;
            default -> 1;
        };
    }

    @Override
    protected String connectionAddress(DeviceDO device, IndustrialDeviceConfig config) {
        String host = StrUtil.blankToDefault(config.getHost(), device.getIpAddress());
        return host + ":" + (config.getPort() == null ? 502 : config.getPort());
    }
}
