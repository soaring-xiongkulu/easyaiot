package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.PlaybackRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class PlaybackService {

    private final PlaybackRepository playbackRepository;

    public Map<String, Object> list(int pageNo, int pageSize, String search, String deviceId) {
        List<Map<String, Object>> items = playbackRepository.list(pageNo, pageSize, deviceId, search);
        return Map.of(
                "items", items,
                "total", playbackRepository.count(deviceId, search)
        );
    }
}
