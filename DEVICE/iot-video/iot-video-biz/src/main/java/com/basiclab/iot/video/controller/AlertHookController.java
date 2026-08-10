package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.AlertHookService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/alert")
@RequiredArgsConstructor
public class AlertHookController {

    private final AlertHookService alertHookService;

    @PostMapping("/hook")
    public VideoApiResponse<Map<String, Object>> hook(@RequestBody Map<String, Object> body) {
        Map<String, Object> result = alertHookService.processHook(body);
        String status = String.valueOf(result.getOrDefault("status", ""));
        if ("success".equals(status)) {
            return VideoApiResponse.success("告警事件已发送", result);
        }
        if ("skipped".equals(status) || "suppressed".equals(status)) {
            return VideoApiResponse.success("告警事件已跳过", result);
        }
        return VideoApiResponse.error(500, "告警事件处理失败: " + result.getOrDefault("error", "未知错误"));
    }
}
