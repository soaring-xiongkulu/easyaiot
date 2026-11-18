package com.basiclab.iot.sink.protocol.modbus;

import com.basiclab.iot.sink.protocol.polling.IndustrialDeviceConfig;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;

class IotModbusPollingProtocolTest {

    @Test
    void shouldApplyIntegerScaleWithoutBinaryFloatingPointArtifacts() {
        IndustrialDeviceConfig.Point point = new IndustrialDeviceConfig.Point();
        point.setDataType("UINT16");
        point.setScale(0.1D);

        Object value = IotModbusPollingProtocol.decodeRegisters(new byte[]{0x01, 0x1F}, point);

        assertEquals("28.7", ((BigDecimal) value).toPlainString());
    }
}
