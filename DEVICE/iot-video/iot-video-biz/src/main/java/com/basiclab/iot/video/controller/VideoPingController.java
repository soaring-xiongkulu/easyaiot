package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/video")
public class VideoPingController {

    @GetMapping("/ping")
    public VideoApiResponse<Map<String, String>> ping() {
        return VideoApiResponse.success(Map.of("service", "video-server-java", "phase", "0"));
    }
}
