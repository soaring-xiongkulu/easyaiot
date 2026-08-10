package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.DeviceDetectionRegionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
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

    @PostMapping("/device/{deviceId}/regions")
    public VideoApiResponse<Map<String, Object>> create(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> body) {
        return VideoApiResponse.success("创建成功", regionService.createRegion(deviceId, body));
    }

    @PutMapping("/region/{regionId}")
    public VideoApiResponse<Map<String, Object>> update(
            @PathVariable int regionId,
            @RequestBody Map<String, Object> body) {
        return VideoApiResponse.success("更新成功", regionService.updateRegion(regionId, body));
    }

    @DeleteMapping("/region/{regionId}")
    public VideoApiResponse<Void> delete(@PathVariable int regionId) {
        regionService.deleteRegion(regionId);
        return VideoApiResponse.success("删除成功", null);
    }

    @PostMapping("/device/{deviceId}/cover-image")
    public VideoApiResponse<Map<String, Object>> updateCoverImage(@PathVariable String deviceId) {
        return VideoApiResponse.success("更新封面图成功", regionService.updateCoverImage(deviceId));
    }

    @PostMapping("/device/{deviceId}/snapshot")
    public VideoApiResponse<Map<String, Object>> captureSnapshot(@PathVariable String deviceId) {
        return VideoApiResponse.success("抓拍成功", regionService.captureSnapshot(deviceId));
    }
}
