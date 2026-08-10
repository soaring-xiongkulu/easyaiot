package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.FaceMatchingService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/face/matching")
@RequiredArgsConstructor
public class FaceMatchingController {

    private final FaceMatchingService faceMatchingService;

    @PostMapping("/publish")
    public VideoApiResponse<Map<String, Object>> publish(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> message = faceMatchingService.publish(body);
        return VideoApiResponse.success("投递成功", message);
    }

    @PostMapping("/process")
    public VideoApiResponse<Map<String, Object>> process(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> record = faceMatchingService.process(body);
        return VideoApiResponse.success("处理成功", record);
    }
}
