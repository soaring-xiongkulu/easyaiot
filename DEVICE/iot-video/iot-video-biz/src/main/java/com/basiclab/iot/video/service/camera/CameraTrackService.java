package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.TrackRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class CameraTrackService {

    private final TrackRepository trackRepository;

    public List<Map<String, Object>> listSessions(String deviceId, String begin, String end, int limit) {
        return trackRepository.listSessions(deviceId, begin, end, limit);
    }

    public List<Map<String, Object>> listPoints(Long sessionId, String deviceId, String begin, String end, int limit) {
        if (sessionId == null && (deviceId == null || deviceId.isBlank())) {
            throw new VideoBusinessException(400, "请提供 session_id 或 device_id");
        }
        return trackRepository.listPoints(sessionId, deviceId, begin, end, limit);
    }
}
