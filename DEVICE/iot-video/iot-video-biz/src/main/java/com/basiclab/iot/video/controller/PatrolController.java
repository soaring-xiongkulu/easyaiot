package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.PatrolSessionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/video/patrol")
@RequiredArgsConstructor
public class PatrolController {

    private final PatrolSessionService patrolSessionService;

    @PostMapping("/session")
    public VideoApiResponse<Map<String, Object>> createSession(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success(patrolSessionService.createSession(body != null ? body : Map.of()));
    }

    @GetMapping("/session/{sessionId}")
    public Object getSession(@PathVariable long sessionId) {
        try {
            return VideoApiResponse.success(patrolSessionService.getSession(sessionId));
        } catch (VideoBusinessException ex) {
            if (ex.getCode() == 404) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(VideoApiResponse.error(404, ex.getMessage()));
            }
            throw ex;
        }
    }

    @PostMapping("/session/{sessionId}/start")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> startSession(@PathVariable long sessionId) {
        Map<String, Object> result = patrolSessionService.startSession(sessionId);
        boolean ok = Boolean.TRUE.equals(result.get("ok"));
        String message = String.valueOf(result.get("message"));
        @SuppressWarnings("unchecked")
        Map<String, Object> data = (Map<String, Object>) result.get("data");
        VideoApiResponse<Map<String, Object>> body = new VideoApiResponse<>();
        body.setCode(ok ? 0 : 400);
        body.setMsg(message);
        body.setMessage(message);
        body.setData(data);
        return ResponseEntity.status(ok ? HttpStatus.OK : HttpStatus.BAD_REQUEST).body(body);
    }

    @PostMapping("/session/{sessionId}/stop")
    public VideoApiResponse<Map<String, Object>> stopSession(@PathVariable long sessionId) {
        Map<String, Object> result = patrolSessionService.stopSession(sessionId);
        @SuppressWarnings("unchecked")
        Map<String, Object> data = (Map<String, Object>) result.get("data");
        return VideoApiResponse.success(String.valueOf(result.get("message")), data);
    }

    @GetMapping("/session/{sessionId}/stats")
    public Object sessionStats(@PathVariable long sessionId) {
        try {
            return VideoApiResponse.success(patrolSessionService.buildStats(sessionId));
        } catch (VideoBusinessException ex) {
            if (ex.getCode() == 404) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(VideoApiResponse.error(404, ex.getMessage()));
            }
            throw ex;
        }
    }

    @GetMapping(value = "/session/{sessionId}/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Object sessionEvents(@PathVariable long sessionId) {
        try {
            return patrolSessionService.subscribeEvents(sessionId);
        } catch (VideoBusinessException ex) {
            if (ex.getCode() == 404) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(VideoApiResponse.error(404, ex.getMessage()));
            }
            throw ex;
        }
    }

    @GetMapping("/directory/{directoryId}/devices")
    public VideoApiResponse<Map<String, Object>> directoryDevices(
            @PathVariable int directoryId,
            @RequestParam(defaultValue = "1") String include_children) {
        boolean includeChildren = !("0".equals(include_children) || "false".equalsIgnoreCase(include_children));
        return VideoApiResponse.success(patrolSessionService.resolveDirectoryDevices(directoryId, includeChildren));
    }

    @PatchMapping("/session/{sessionId}")
    public Object patchSession(
            @PathVariable long sessionId,
            @RequestBody(required = false) Map<String, Object> body) {
        try {
            return VideoApiResponse.success(patrolSessionService.patchSession(sessionId, body != null ? body : Map.of()));
        } catch (VideoBusinessException ex) {
            if (ex.getCode() == 404) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(VideoApiResponse.error(404, ex.getMessage()));
            }
            throw ex;
        }
    }

    @PostMapping("/heartbeat")
    public ResponseEntity<VideoApiResponse<Void>> heartbeat(@RequestBody(required = false) Map<String, Object> body) {
        if (!patrolSessionService.receiveHeartbeat(body)) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(VideoApiResponse.error(400, "无效心跳"));
        }
        return ResponseEntity.ok(VideoApiResponse.success("心跳接收成功", null));
    }
}
