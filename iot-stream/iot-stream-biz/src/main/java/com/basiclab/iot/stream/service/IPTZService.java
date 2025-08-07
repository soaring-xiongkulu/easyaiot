package com.basiclab.iot.stream.service;


import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.Preset;

import java.util.List;

public interface IPTZService {


    List<Preset> queryPresetList(String deviceId, String channelDeviceId);

    void addPreset(Preset preset);

    void deletePreset(Integer qq);

    void ptz(Device device, String channelId, int cmdCode, int horizonSpeed, int verticalSpeed, int zoomSpeed);

    void frontEndCommand(Device device, String channelId, int cmdCode, int parameter1, int parameter2, int combindCode2);

    void frontEndCommand(CommonGBChannel channel, Integer cmdCode, Integer parameter1, Integer parameter2, Integer combindCode2);
}
