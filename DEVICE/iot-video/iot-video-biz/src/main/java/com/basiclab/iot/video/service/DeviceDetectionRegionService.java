package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.DeviceDetectionRegionRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class DeviceDetectionRegionService {

    private final DeviceDetectionRegionRepository regionRepository;

    public List<Map<String, Object>> listByDevice(String deviceId) {
        if (!regionRepository.deviceExists(deviceId)) {
            throw new VideoBusinessException(400, "设备不存在: ID=" + deviceId);
        }
        return regionRepository.listByDevice(deviceId);
    }
}
