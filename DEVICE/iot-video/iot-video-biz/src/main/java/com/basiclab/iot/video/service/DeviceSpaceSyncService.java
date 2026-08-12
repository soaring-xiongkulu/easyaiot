package com.basiclab.iot.video.service;

import com.basiclab.iot.video.dal.DeviceDirectoryRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.dal.DeviceSpaceRepository;
import com.basiclab.iot.video.dal.RecordSpaceRepository;
import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.domain.DeviceDirectoryRow;
import com.basiclab.iot.video.domain.DeviceRow;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Optional;

/**
 * Mirrors Python {@code ensure_device_spaces} and {@code sync_device_spaces_to_directory}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DeviceSpaceSyncService {

    private final DeviceRepository deviceRepository;
    private final DeviceSpaceRepository deviceSpaceRepository;
    private final SnapSpaceRepository snapSpaceRepository;
    private final RecordSpaceRepository recordSpaceRepository;
    private final DeviceDirectoryRepository directoryRepository;

    public void ensureDeviceSpaces(String deviceId) {
        Optional<DeviceRow> deviceOpt = deviceRepository.findById(deviceId);
        if (deviceOpt.isEmpty()) {
            return;
        }
        DeviceRow device = deviceOpt.get();
        try {
            if (deviceSpaceRepository.findSnapSpaceByDeviceId(deviceId).isEmpty()) {
                deviceSpaceRepository.createSnapSpace(deviceId, device.getName());
                log.info("设备 {} 的抓拍空间已自动创建", deviceId);
            }
            if (deviceSpaceRepository.findRecordSpaceByDeviceId(deviceId).isEmpty()) {
                deviceSpaceRepository.createRecordSpace(deviceId, device.getName());
                log.info("设备 {} 的监控录像空间已自动创建", deviceId);
            }
        } catch (Exception ex) {
            log.warn("检查设备 {} 空间失败: {}", deviceId, ex.getMessage());
        }
    }

    public void syncDeviceSpacesToDirectory(String deviceId, Integer directoryId) {
        Optional<DeviceDirectoryRow> directory = directoryId != null
                ? directoryRepository.findById(directoryId)
                : Optional.empty();
        int snapSave = directory.map(DeviceDirectoryRow::getSnapSaveTime).orElse(1);
        int recordSave = directory.map(DeviceDirectoryRow::getRecordSaveTime).orElse(1);

        snapSpaceRepository.findByDeviceId(deviceId).ifPresent(space -> {
            if (!Boolean.TRUE.equals(space.get("save_time_custom"))) {
                snapSpaceRepository.updateFields(((Number) space.get("id")).intValue(), Map.of("save_time", snapSave));
            }
        });
        recordSpaceRepository.findByDeviceId(deviceId).ifPresent(space -> {
            if (!Boolean.TRUE.equals(space.get("save_time_custom"))) {
                recordSpaceRepository.updateFields(((Number) space.get("id")).intValue(), Map.of("save_time", recordSave));
            }
        });
    }

    public int propagateDirectorySaveTime(int directoryId, Integer snapSaveTime, Integer recordSaveTime) {
        int updated = 0;
        if (snapSaveTime != null) {
            updated += snapSpaceRepository.updateSaveTimeForDirectory(directoryId, snapSaveTime);
        }
        if (recordSaveTime != null) {
            updated += recordSpaceRepository.updateSaveTimeForDirectory(directoryId, recordSaveTime);
        }
        return updated;
    }
}
