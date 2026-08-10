package com.basiclab.iot.video.util;

import com.basiclab.iot.video.exception.VideoBusinessException;

import java.util.regex.Pattern;

/** Reject path traversal and unsafe characters before using IDs in filesystem paths. */
public final class PathSegmentSanitizer {

    private static final Pattern SAFE_SEGMENT = Pattern.compile("^[A-Za-z0-9][A-Za-z0-9._-]*$");

    private PathSegmentSanitizer() {
    }

    public static String sanitizeDeviceId(String deviceId) {
        return sanitizeSegment(deviceId, "deviceId");
    }

    public static String sanitizeSegment(String value, String label) {
        if (value == null || value.isBlank()) {
            throw new VideoBusinessException(400, label + " is required");
        }
        String trimmed = value.trim();
        if (trimmed.contains("..")
                || trimmed.indexOf('/') >= 0
                || trimmed.indexOf('\\') >= 0
                || trimmed.indexOf('\0') >= 0) {
            throw new VideoBusinessException(400, "invalid " + label + " for filesystem path");
        }
        if (!SAFE_SEGMENT.matcher(trimmed).matches()) {
            throw new VideoBusinessException(400, "invalid " + label + " characters");
        }
        return trimmed;
    }
}
