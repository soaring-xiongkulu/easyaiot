package com.basiclab.iot.video.service.ops;

import com.basiclab.iot.video.dal.RecordFileRepository;
import com.basiclab.iot.video.dal.RecordSpaceRepository;
import com.basiclab.iot.video.support.SpaceSaveTimeSupport;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Scheduled record-space cleanup aligned with Python {@code auto_cleanup_all_record_spaces}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RecordSpaceCleanupService {

    private final RecordSpaceRepository recordSpaceRepository;
    private final RecordFileRepository recordFileRepository;

    public Map<String, Object> cleanupAllSpaces() {
        List<Map<String, Object>> spaces = recordSpaceRepository.listAllSpaces();
        int totalProcessed = 0;
        int totalDeleted = 0;
        int totalErrors = 0;

        for (Map<String, Object> space : spaces) {
            int saveTimeHours = SpaceSaveTimeSupport.effectiveSaveTimeHours(space);
            if (saveTimeHours <= 0) {
                continue;
            }
            int spaceId = ((Number) space.get("id")).intValue();
            String deviceId = space.get("device_id") != null ? String.valueOf(space.get("device_id")) : null;
            try {
                Timestamp cutoff = SpaceSaveTimeSupport.cutoffBefore(saveTimeHours);
                int deleted = recordFileRepository.deleteExpiredBefore(spaceId, deviceId, cutoff);
                totalProcessed += deleted;
                totalDeleted += deleted;
                if (deleted > 0) {
                    log.info(
                            "录像空间清理完成: spaceId={} name={} deleted={}",
                            spaceId,
                            space.get("space_name"),
                            deleted
                    );
                }
            } catch (Exception e) {
                totalErrors++;
                log.error(
                        "清理录像空间失败: spaceId={} name={} error={}",
                        spaceId,
                        space.get("space_name"),
                        e.getMessage(),
                        e
                );
            }
        }

        log.info(
                "所有录像空间自动清理完成: processed={} deleted={} errors={}",
                totalProcessed,
                totalDeleted,
                totalErrors
        );
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("processed_count", totalProcessed);
        result.put("deleted_count", totalDeleted);
        result.put("archived_count", 0);
        result.put("error_count", totalErrors);
        result.put("orphan_deleted_count", 0);
        result.put("orphan_scanned_count", 0);
        result.put("orphan_error_count", 0);
        return result;
    }
}
