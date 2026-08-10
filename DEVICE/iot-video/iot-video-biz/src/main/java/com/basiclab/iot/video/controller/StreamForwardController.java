package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.StreamForwardService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/stream-forward")
@RequiredArgsConstructor
public class StreamForwardController {

    private final StreamForwardService streamForwardService;

    @GetMapping("/task/{taskId}")
    public VideoApiResponse<Map<String, Object>> getTask(@PathVariable long taskId) {
        return VideoApiResponse.success(streamForwardService.getTask(taskId));
    }

    @PostMapping("/task/{taskId}/start")
    public VideoApiResponse<Map<String, Object>> start(@PathVariable long taskId) {
        Map<String, Object> result = streamForwardService.start(taskId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @PostMapping("/task/{taskId}/stop")
    public VideoApiResponse<Map<String, Object>> stop(@PathVariable long taskId) {
        Map<String, Object> result = streamForwardService.stop(taskId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @GetMapping("/task/{taskId}/status")
    public VideoApiResponse<Map<String, Object>> status(@PathVariable long taskId) {
        return VideoApiResponse.success(streamForwardService.taskStatus(taskId));
    }
}
