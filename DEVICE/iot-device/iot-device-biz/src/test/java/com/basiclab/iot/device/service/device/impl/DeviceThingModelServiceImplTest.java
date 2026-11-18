package com.basiclab.iot.device.service.device.impl;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

class DeviceThingModelServiceImplTest {

    @Test
    void shouldKeepParsedValuesSeparateFromNestedRawPayloads() {
        String payload = "{temperature:2.5,setpoint:30,running:false,_raw:{temperature:01 03 02 00 19," +
                "setpoint:01 03 02 00 1E,running:01 01 01 00}}";

        JSONObject params = DeviceThingModelServiceImpl.parseParams(payload);

        assertNotNull(params);
        assertEquals("2.5", String.valueOf(params.get("temperature")));
        assertEquals("30", String.valueOf(params.get("setpoint")));
        assertFalse(params.getBooleanValue("running"));
        JSONObject raw = params.getJSONObject("_raw");
        assertNotNull(raw);
        assertEquals("01 03 02 00 19", raw.getString("temperature"));
        assertEquals("01 03 02 00 1E", raw.getString("setpoint"));
        assertEquals("01 01 01 00", raw.getString("running"));
    }

    @Test
    void shouldExposeCustomPointNameAndClampDecimalPlaces() {
        TDDeviceDataResp temperature = new TDDeviceDataResp();
        temperature.setPropertyCode("temperature");
        temperature.setPropertyName("温度");
        TDDeviceDataResp legacy = new TDDeviceDataResp();
        legacy.setPropertyCode("running");
        legacy.setPropertyName("运行");
        List<TDDeviceDataResp> rows = new ArrayList<>(List.of(temperature, legacy));
        String extension = "{\"protocolConfig\":{\"points\":[" +
                "{\"propertyCode\":\"temperature\",\"identifier\":\"一号探头温度\",\"decimalPlaces\":12}," +
                "{\"propertyCode\":\"running\",\"identifier\":\"running\",\"decimalPlaces\":0}]}}";

        DeviceThingModelServiceImpl.applyPointDisplayConfig(rows, extension);

        assertEquals("一号探头温度", temperature.getPointName());
        assertEquals(10, temperature.getDecimalPlaces());
        assertNull(legacy.getPointName());
        assertEquals(0, legacy.getDecimalPlaces());
    }
}
