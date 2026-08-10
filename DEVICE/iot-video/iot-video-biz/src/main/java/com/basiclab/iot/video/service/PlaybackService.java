package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.PlaybackRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class PlaybackService {

    private final PlaybackRepository playbackRepository;

    public Map<String, Object> list(int pageNo, int pageSize, String search, String deviceId,
                                    String startTime, String endTime) {
        Timestamp start = parseIso(startTime, "开始时间格式错误");
        Timestamp end = parseIso(endTime, "结束时间格式错误");
        List<Map<String, Object>> items = playbackRepository.list(pageNo, pageSize, deviceId, search, start, end);
        return Map.of(
                "items", items,
                "total", playbackRepository.count(deviceId, search, start, end)
        );
    }

    public Map<String, Object> get(int playbackId) {
        return playbackRepository.findById(playbackId)
                .orElseThrow(() -> new VideoBusinessException(400, "录像回放不存在: ID=" + playbackId));
    }

    public Map<String, Object> create(Map<String, Object> data) {
        for (String field : List.of("file_path", "event_time", "device_id", "device_name", "duration")) {
            if (!data.containsKey(field) || data.get(field) == null || String.valueOf(data.get(field)).isBlank()) {
                throw new VideoBusinessException(400, field + "不能为空");
            }
        }
        Timestamp eventTime = parseIso(String.valueOf(data.get("event_time")), "event_time格式错误，应为ISO格式");
        Map<String, Object> fields = new LinkedHashMap<>(data);
        fields.put("event_time", eventTime);
        int id = playbackRepository.insert(fields);
        return get(id);
    }

    public Map<String, Object> update(int playbackId, Map<String, Object> data) {
        playbackRepository.findById(playbackId)
                .orElseThrow(() -> new VideoBusinessException(400, "录像回放不存在: ID=" + playbackId));
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("file_path")) {
            fields.put("file_path", data.get("file_path"));
        }
        if (data.containsKey("event_time")) {
            fields.put("event_time", parseIso(String.valueOf(data.get("event_time")), "event_time格式错误"));
        }
        if (data.containsKey("device_id")) {
            fields.put("device_id", data.get("device_id"));
        }
        if (data.containsKey("device_name")) {
            fields.put("device_name", data.get("device_name"));
        }
        if (data.containsKey("duration")) {
            fields.put("duration", data.get("duration"));
        }
        if (data.containsKey("thumbnail_path")) {
            fields.put("thumbnail_path", data.get("thumbnail_path"));
        }
        if (data.containsKey("file_size")) {
            fields.put("file_size", data.get("file_size"));
        }
        playbackRepository.updateFields(playbackId, fields);
        return get(playbackId);
    }

    public void delete(int playbackId) {
        playbackRepository.findById(playbackId)
                .orElseThrow(() -> new VideoBusinessException(400, "录像回放不存在: ID=" + playbackId));
        playbackRepository.delete(playbackId);
    }

    public Map<String, Object> thumbnail(int playbackId) {
        Map<String, Object> playback = get(playbackId);
        Object thumb = playback.get("thumbnail_path");
        if (thumb == null || String.valueOf(thumb).isBlank()) {
            throw new VideoBusinessException(400, "该录像没有封面图");
        }
        return Map.of("thumbnail_path", thumb);
    }

    public Map<String, Object> statistics(String deviceId, String startTime, String endTime) {
        Timestamp start = parseIso(startTime, "开始时间格式错误");
        Timestamp end = parseIso(endTime, "结束时间格式错误");
        return playbackRepository.statistics(deviceId, start, end);
    }

    private static Timestamp parseIso(String value, String errorMsg) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            String text = value.trim().replace("Z", "+00:00");
            return Timestamp.from(Instant.parse(text));
        } catch (Exception e) {
            throw new VideoBusinessException(400, errorMsg);
        }
    }
}
