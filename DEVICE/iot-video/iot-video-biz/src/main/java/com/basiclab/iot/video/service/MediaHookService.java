package com.basiclab.iot.video.service;

import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class MediaHookService {

    /**
     * Certify parity: accept snap-completed hook and acknowledge (no MinIO upload in P2-S2).
     */
    public void snapCompleted(Map<String, Object> payload) {
        if (payload == null) {
            return;
        }
        String deviceId = payload.get("device_id") != null ? String.valueOf(payload.get("device_id")).trim() : "";
        String filePath = payload.get("file_path") != null ? String.valueOf(payload.get("file_path")).trim() : "";
        if (filePath.isEmpty() && payload.get("file") != null) {
            filePath = String.valueOf(payload.get("file")).trim();
        }
        if (deviceId.isEmpty() || filePath.isEmpty()) {
            return;
        }
    }
}
