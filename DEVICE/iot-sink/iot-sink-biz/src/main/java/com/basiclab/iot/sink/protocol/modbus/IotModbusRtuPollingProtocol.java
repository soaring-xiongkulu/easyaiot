package com.basiclab.iot.sink.protocol.modbus;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import com.basiclab.iot.sink.dal.mapper.DeviceMapper;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.protocol.polling.AbstractIndustrialPollingProtocol;
import com.basiclab.iot.sink.protocol.polling.IndustrialDeviceConfig;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import com.ghgande.j2mod.modbus.facade.ModbusSerialMaster;
import com.ghgande.j2mod.modbus.procimg.InputRegister;
import com.ghgande.j2mod.modbus.procimg.Register;
import com.ghgande.j2mod.modbus.procimg.SimpleRegister;
import com.ghgande.j2mod.modbus.util.SerialParameters;
import lombok.extern.slf4j.Slf4j;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;

/** Modbus RTU master polling over an RS-485 serial interface. */
@Slf4j
public class IotModbusRtuPollingProtocol extends AbstractIndustrialPollingProtocol {

    public static final String PROTOCOL_TYPE = "MODBUS_RTU";

    private final Map<String, PooledSerialMaster> masters = new ConcurrentHashMap<>();

    private static final class PooledSerialMaster {
        private final String fingerprint;
        private final ModbusSerialMaster master;

        private PooledSerialMaster(String fingerprint, ModbusSerialMaster master) {
            this.fingerprint = fingerprint;
            this.master = master;
        }
    }

    public IotModbusRtuPollingProtocol(IotGatewayProperties.PollingProtocolProperties properties,
                                       DeviceMapper deviceMapper,
                                       IotDeviceMessageService messageService,
                                       IotMessageBus messageBus,
                                       DeviceServerIdService deviceServerIdService,
                                       String serverId) {
        super(PROTOCOL_TYPE, serverId, properties, deviceMapper, messageService, messageBus,
                deviceServerIdService);
    }

    @Override
    protected Map<String, Object> poll(DeviceDO device, IndustrialDeviceConfig config) throws Exception {
        synchronized (portLock(config)) {
            return pollSerial(config);
        }
    }

    private Map<String, Object> pollSerial(IndustrialDeviceConfig config) throws Exception {
        ModbusSerialMaster master = acquireMaster(config);
        int unitId = config.getUnitId() == null ? 1 : config.getUnitId();
        Map<String, Object> values = new LinkedHashMap<>();
        Map<String, String> rawValues = new LinkedHashMap<>();
        for (IndustrialDeviceConfig.Point point : config.getPoints()) {
            if (point == null || !point.hasResolvedPropertyCode() || point.getAddress() == null) {
                continue;
            }
            String propertyCode = point.resolvedPropertyCode();
            IotModbusPollingProtocol.PointReadResult result = readPoint(master, unitId, point);
            values.put(propertyCode, result.value());
            rawValues.put(propertyCode, result.rawPayload());
        }
        if (!rawValues.isEmpty()) {
            values.put("_raw", rawValues);
        }
        return values;
    }

    @Override
    protected void write(DeviceDO device, IndustrialDeviceConfig config, IotDeviceMessage message) throws Exception {
        synchronized (portLock(config)) {
            writeSerial(config, message);
        }
    }

    private void writeSerial(IndustrialDeviceConfig config, IotDeviceMessage message) throws Exception {
        ModbusSerialMaster master = acquireMaster(config);
        int unitId = config.getUnitId() == null ? 1 : config.getUnitId();
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
                boolean state = value instanceof Boolean bool ? bool : Boolean.parseBoolean(String.valueOf(value));
                master.writeCoil(unitId, point.getAddress(), state);
            } else if (value instanceof Number number) {
                Register[] registers = toRegisters(IotModbusPollingProtocol.encodeRegisters(number, point));
                if (registers.length == 1) {
                    master.writeSingleRegister(unitId, point.getAddress(), registers[0]);
                } else {
                    master.writeMultipleRegisters(unitId, point.getAddress(), registers);
                }
            }
        }
    }

    private ModbusSerialMaster acquireMaster(IndustrialDeviceConfig config) throws Exception {
        String port = config.getSerialPort();
        if (StrUtil.isBlank(port)) {
            throw new IllegalArgumentException("Modbus RTU serial port is missing");
        }
        String fingerprint = serialFingerprint(config);
        PooledSerialMaster pooled = masters.get(port);
        if (pooled != null && Objects.equals(pooled.fingerprint, fingerprint) && pooled.master.isConnected()) {
            return pooled.master;
        }
        if (pooled != null) {
            disconnectQuietly(pooled.master);
            masters.remove(port, pooled);
        }
        ModbusSerialMaster master = createMaster(config);
        master.connect();
        masters.put(port, new PooledSerialMaster(fingerprint, master));
        return master;
    }

    private IotModbusPollingProtocol.PointReadResult readPoint(ModbusSerialMaster master, int unitId,
                                                               IndustrialDeviceConfig.Point point) throws Exception {
        String function = StrUtil.blankToDefault(point.getFunction(), "HOLDING_REGISTER").toUpperCase();
        int quantity = Math.max(defaultQuantity(point.getDataType()),
                point.getQuantity() == null ? 1 : point.getQuantity());
        return switch (function) {
            case "COIL" -> {
                boolean value = master.readCoils(unitId, point.getAddress(), quantity).getBit(0);
                byte[] raw = {(byte) (value ? 1 : 0)};
                yield new IotModbusPollingProtocol.PointReadResult(value,
                        IotModbusPollingProtocol.formatResponsePdu(unitId, 0x01, raw));
            }
            case "DISCRETE_INPUT" -> {
                boolean value = master.readInputDiscretes(unitId, point.getAddress(), quantity).getBit(0);
                byte[] raw = {(byte) (value ? 1 : 0)};
                yield new IotModbusPollingProtocol.PointReadResult(value,
                        IotModbusPollingProtocol.formatResponsePdu(unitId, 0x02, raw));
            }
            case "INPUT_REGISTER" -> {
                byte[] raw = toBytes(master.readInputRegisters(unitId, point.getAddress(), quantity));
                yield new IotModbusPollingProtocol.PointReadResult(
                        IotModbusPollingProtocol.decodeRegisters(raw, point),
                        IotModbusPollingProtocol.formatResponsePdu(unitId, 0x04, raw));
            }
            case "HOLDING_REGISTER" -> {
                byte[] raw = toBytes(master.readMultipleRegisters(unitId, point.getAddress(), quantity));
                yield new IotModbusPollingProtocol.PointReadResult(
                        IotModbusPollingProtocol.decodeRegisters(raw, point),
                        IotModbusPollingProtocol.formatResponsePdu(unitId, 0x03, raw));
            }
            default -> throw new IllegalArgumentException("Unsupported Modbus function: " + function);
        };
    }

    private ModbusSerialMaster createMaster(IndustrialDeviceConfig config) {
        SerialParameters parameters = new SerialParameters();
        parameters.setPortName(config.getSerialPort());
        parameters.setBaudRate(config.getBaudRate() == null ? 9600 : config.getBaudRate());
        parameters.setDatabits(config.getDataBits() == null ? 8 : config.getDataBits());
        parameters.setStopbits(StrUtil.blankToDefault(config.getStopBits(), "1"));
        parameters.setParity(StrUtil.blankToDefault(config.getParity(), "NONE"));
        parameters.setEncoding("rtu");
        parameters.setRs485Mode(!Boolean.FALSE.equals(config.getRs485Mode()));
        return new ModbusSerialMaster(parameters, (int) requestTimeoutMs(),
                config.getTransmitDelayMs() == null ? 0 : Math.max(0, config.getTransmitDelayMs()));
    }

    @Override
    protected void invalidateConnection(DeviceDO device, IndustrialDeviceConfig config) {
        String port = config.getSerialPort();
        if (StrUtil.isBlank(port)) {
            return;
        }
        synchronized (portLock(config)) {
            PooledSerialMaster pooled = masters.remove(port);
            if (pooled != null) {
                disconnectQuietly(pooled.master);
            }
        }
    }

    @Override
    protected void closeConnections() {
        for (PooledSerialMaster pooled : masters.values()) {
            disconnectQuietly(pooled.master);
        }
        masters.clear();
    }

    private static void disconnectQuietly(ModbusSerialMaster master) {
        if (master == null) {
            return;
        }
        try {
            master.disconnect();
        } catch (Exception e) {
            log.debug("[disconnectQuietly][modbus rtu disconnect failed]", e);
        }
    }

    private static String serialFingerprint(IndustrialDeviceConfig config) {
        return String.join("|",
                StrUtil.nullToEmpty(config.getSerialPort()),
                String.valueOf(config.getBaudRate() == null ? 9600 : config.getBaudRate()),
                String.valueOf(config.getDataBits() == null ? 8 : config.getDataBits()),
                StrUtil.blankToDefault(config.getStopBits(), "1"),
                StrUtil.blankToDefault(config.getParity(), "NONE"),
                String.valueOf(config.getTransmitDelayMs() == null ? 0 : config.getTransmitDelayMs()),
                String.valueOf(!Boolean.FALSE.equals(config.getRs485Mode())));
    }

    private Object portLock(IndustrialDeviceConfig config) {
        return ModbusSerialPortLocks.forPort(config.getSerialPort());
    }

    private byte[] toBytes(InputRegister[] registers) {
        ByteBuffer buffer = ByteBuffer.allocate(registers.length * 2).order(ByteOrder.BIG_ENDIAN);
        for (InputRegister register : registers) {
            buffer.putShort((short) register.getValue());
        }
        return buffer.array();
    }

    private Register[] toRegisters(byte[] bytes) {
        ByteBuffer buffer = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN);
        Register[] registers = new Register[bytes.length / 2];
        for (int index = 0; index < registers.length; index++) {
            registers[index] = new SimpleRegister(buffer.getShort() & 0xffff);
        }
        return registers;
    }

    private int defaultQuantity(String dataType) {
        return switch (StrUtil.blankToDefault(dataType, "UINT16").toUpperCase()) {
            case "INT32", "UINT32", "FLOAT32" -> 2;
            case "INT64", "FLOAT64" -> 4;
            default -> 1;
        };
    }

    @Override
    protected String connectionAddress(DeviceDO device, IndustrialDeviceConfig config) {
        return config.getSerialPort();
    }
}
