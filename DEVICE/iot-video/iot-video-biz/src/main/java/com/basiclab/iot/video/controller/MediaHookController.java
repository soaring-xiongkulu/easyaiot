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

    @PostMapping("/srs/on_dvr")
    public VideoApiResponse<Void> srsOnDvr(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.srsOnDvr(body);
        return hookOk();
    }

    @PostMapping("/srs/on_publish")
    public VideoApiResponse<Void> srsOnPublish(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.srsOnPublish(body);
        return hookOk();
    }

    @PostMapping("/srs/on_unpublish")
    public VideoApiResponse<Void> srsOnUnpublish(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.srsOnUnpublish(body);
        return hookOk();
    }

    @PostMapping("/snap/completed")
    public VideoApiResponse<Void> snapCompleted(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.snapCompleted(body);
        return hookOk();
    }

    @PostMapping("/zlm/on_record_mp4")
    public VideoApiResponse<Void> zlmOnRecordMp4(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.zlmOnRecord(body);
        return hookOk();
    }

    @PostMapping("/zlm/on_record_ts")
    public VideoApiResponse<Void> zlmOnRecordTs(@RequestBody(required = false) Map<String, Object> body) {
        mediaHookService.zlmOnRecord(body);
        return hookOk();
    }

    private static VideoApiResponse<Void> hookOk() {
        VideoApiResponse<Void> response = new VideoApiResponse<>();
        response.setCode(0);
        response.setMsg(null);
        response.setMessage(null);
        return response;
    }
}
