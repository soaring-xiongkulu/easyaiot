package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.CameraService;
import com.basiclab.iot.video.service.ViewForwardService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/camera")
@RequiredArgsConstructor
public class CameraController {

    private final CameraService cameraService;
    private final ViewForwardService viewForwardService;

    @GetMapping("/list")
    public VideoApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search) {
        Map<String, Object> result = cameraService.listDevices(pageNo, pageSize, search);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) result.get("items");
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        Object total = result.get("total");
        if (total instanceof Number number) {
            response.setTotal(number.intValue());
        }
        return response;
    }

    @GetMapping("/device/{deviceId}")
    public VideoApiResponse<Map<String, Object>> get(@PathVariable String deviceId) {
        return VideoApiResponse.success(cameraService.getDevice(deviceId));
    }

    @PostMapping("/device/{deviceId}/stream/start")
    public VideoApiResponse<Map<String, Object>> startStream(@PathVariable String deviceId) {
        Map<String, Object> result = viewForwardService.startStream(deviceId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @PostMapping("/device/{deviceId}/stream/stop")
    public VideoApiResponse<Map<String, Object>> stopStream(@PathVariable String deviceId) {
        Map<String, Object> result = viewForwardService.stopStream(deviceId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @GetMapping("/device/{deviceId}/stream/status")
    public VideoApiResponse<Map<String, Object>> streamStatus(@PathVariable String deviceId) {
        return VideoApiResponse.success(viewForwardService.streamStatus(deviceId));
    }
}
