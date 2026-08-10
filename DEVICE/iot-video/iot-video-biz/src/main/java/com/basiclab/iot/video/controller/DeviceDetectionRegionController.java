package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.DeviceDetectionRegionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/device-detection")
@RequiredArgsConstructor
public class DeviceDetectionRegionController {

    private final DeviceDetectionRegionService regionService;

    @GetMapping("/device/{deviceId}/regions")
    public VideoApiResponse<List<Map<String, Object>>> list(@PathVariable String deviceId) {
        return VideoApiResponse.success(regionService.listByDevice(deviceId));
    }
}
