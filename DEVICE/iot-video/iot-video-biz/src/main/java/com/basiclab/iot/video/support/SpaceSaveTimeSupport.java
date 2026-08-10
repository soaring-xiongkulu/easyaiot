package com.basiclab.iot.video.support;

import java.sql.Timestamp;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;

/**
 * Effective save-time resolution for scheduled space cleanup (mini/DB path).
 */
public final class SpaceSaveTimeSupport {

    private SpaceSaveTimeSupport() {
    }

    public static int effectiveSaveTimeHours(Map<String, Object> space) {
        if (space == null || space.isEmpty()) {
            return 0;
        }
        Object saveTimeObj = space.get("save_time");
        int saveTime = saveTimeObj instanceof Number n ? n.intValue() : 1;
        if (saveTime <= 0) {
            return 0;
        }
        boolean custom = Boolean.TRUE.equals(space.get("save_time_custom"));
        if (custom) {
            return saveTime;
        }
        Object directorySaveTime = space.get("directory_save_time");
        if (directorySaveTime instanceof Number dirHours && dirHours.intValue() > 0) {
            return dirHours.intValue();
        }
        return saveTime;
    }

    public static Timestamp cutoffBefore(int saveTimeHours) {
        if (saveTimeHours <= 0) {
            return null;
        }
        Instant cutoff = Instant.now().minus(saveTimeHours, ChronoUnit.HOURS);
        return Timestamp.from(cutoff);
    }
}
