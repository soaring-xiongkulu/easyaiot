package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.MediaHookService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/media/hook")
@RequiredArgsConstructor
public class MediaHookController {

    private final MediaHookService mediaHookService;

    @PostMapping("/snap/completed")
    public VideoApiResponse<Void> snapCompleted(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.snapCompleted(body);
        VideoApiResponse<Void> response = new VideoApiResponse<>();
        response.setCode(0);
        response.setMsg(null);
        response.setMessage(null);
        return response;
    }
}
