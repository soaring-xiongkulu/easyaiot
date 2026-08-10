package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.talk.AudioTalkService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/camera/audio/talk")
@RequiredArgsConstructor
public class AudioTalkController {

    private final AudioTalkService audioTalkService;

    @GetMapping("/capabilities")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> capabilities(
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String camera_id) {
        String deviceId = device_id != null && !device_id.isBlank() ? device_id : camera_id;
        if (deviceId == null || deviceId.isBlank()) {
            return response(400, 400, "缺少设备 ID", null);
        }
        Map<String, Object> result = audioTalkService.getCapabilities(deviceId);
        return fromServiceResult(result);
    }

    @PostMapping("/start")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> start(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> result = audioTalkService.startSession(body != null ? body : Map.of());
        return fromServiceResult(result);
    }

    @PostMapping("/stop")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> stop(@RequestBody(required = false) Map<String, Object> body) {
        String sessionId = body != null ? String.valueOf(body.getOrDefault("session_id", "")).trim() : "";
        Map<String, Object> result = audioTalkService.stopSession(sessionId);
        return fromServiceResult(result);
    }

    @PostMapping("/send")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> send(@RequestBody(required = false) Map<String, Object> body) {
        String sessionId = body != null ? String.valueOf(body.getOrDefault("session_id", "")).trim() : "";
        String audioData = body != null ? String.valueOf(body.getOrDefault("audio_data", "")).trim() : "";
        Map<String, Object> result = audioTalkService.sendAudio(sessionId, audioData);
        return fromServiceResult(result);
    }

    @GetMapping("/health")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> health() {
        Map<String, Object> result = audioTalkService.health();
        return fromServiceResult(result);
    }

    @SuppressWarnings("unchecked")
    private ResponseEntity<VideoApiResponse<Map<String, Object>>> fromServiceResult(Map<String, Object> result) {
        int code = ((Number) result.getOrDefault("code", 0)).intValue();
        String msg = String.valueOf(result.getOrDefault("msg", ""));
        Map<String, Object> data = (Map<String, Object>) result.get("data");
        VideoApiResponse<Map<String, Object>> body = new VideoApiResponse<>();
        body.setCode(code);
        body.setMsg(msg);
        body.setMessage(msg);
        body.setData(data);
        return ResponseEntity.ok(body);
    }

    private ResponseEntity<VideoApiResponse<Map<String, Object>>> response(
            int httpStatus, int code, String msg, Map<String, Object> data) {
        VideoApiResponse<Map<String, Object>> body = VideoApiResponse.error(code, msg);
        body.setData(data);
        HttpStatus status = httpStatus >= 400 && httpStatus < 600
                ? HttpStatus.valueOf(httpStatus)
                : HttpStatus.OK;
        return ResponseEntity.status(status).body(body);
    }
}
