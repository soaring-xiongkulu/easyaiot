package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.HeartbeatService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/algorithm/heartbeat")
@RequiredArgsConstructor
public class HeartbeatController {

    private final HeartbeatService heartbeatService;

    @PostMapping("/realtime")
    public VideoApiResponse<Map<String, Object>> realtime(@RequestBody Map<String, Object> body) {
        Map<String, Object> data = heartbeatService.receiveRealtime(body);
        return VideoApiResponse.success("心跳接收成功", data);
    }

    @PostMapping("/patrol")
    public VideoApiResponse<Map<String, Object>> patrol(@RequestBody Map<String, Object> body) {
        Map<String, Object> data = heartbeatService.receivePatrol(body);
        return VideoApiResponse.success("心跳接收成功", data);
    }
}
