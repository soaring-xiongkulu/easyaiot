package com.basiclab.iot.video.service.camera;

import com.basiclab.iot.video.dal.DeviceDirectoryRepository;
import com.basiclab.iot.video.dal.DeviceRepository;
import com.basiclab.iot.video.domain.DeviceDirectoryRow;
import com.basiclab.iot.video.domain.DeviceRow;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.CameraService;
import com.basiclab.iot.video.service.DeviceSpaceSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class CameraDirectoryService {

    private static final String DEFAULT_DIRECTORY_NAME = "默认分组";
    private static final DateTimeFormatter ISO_INSTANT = DateTimeFormatter.ISO_INSTANT;

    private final DeviceDirectoryRepository directoryRepository;
    private final DeviceRepository deviceRepository;
    private final CameraService cameraService;
    private final Gb28181SyncService gb28181SyncService;
    private final DirectoryJsonSyncService directoryJsonSyncService;
    private final DeviceSpaceSyncService deviceSpaceSyncService;

    public List<Map<String, Object>> listTree() {
        gb28181SyncService.ensureDirectoryLayout();
        try {
            gb28181SyncService.syncFromWvp(false, null, null);
        } catch (Exception e) {
            log.warn("目录列表加载前国标同步失败: {}", e.getMessage());
        }
        directoryRepository.ensureDefaultDirectory();
        return buildTree(null);
    }

    public Map<String, Object> monitorTree(boolean skipSync, String authorization, String xAuthorization) {
        gb28181SyncService.ensureDirectoryLayout();
        if (!skipSync) {
            try {
                gb28181SyncService.syncFromWvp(false, authorization, xAuthorization);
            } catch (Exception e) {
                gb28181SyncService.ensureDirectoryLayout();
            }
        }
        directoryRepository.ensureDefaultDirectory();
        List<Map<String, Object>> tree = buildMonitorTree(null);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("tree", tree);
        data.put("unassigned_devices", List.of());
        return data;
    }

    public Map<String, Object> getDirectory(int directoryId) {
        DeviceDirectoryRow directory = directoryRepository.findById(directoryId)
                .orElseThrow(() -> new VideoBusinessException(400, "目录不存在: ID=" + directoryId));
        Map<String, Object> data = directoryToMap(directory);
        data.put("device_count", directoryRepository.countDevices(directoryId));
        data.put("children_count", directoryRepository.countChildren(directoryId));
        return data;
    }

    public Map<String, Object> createDirectory(Map<String, Object> data) {
        String name = str(data.get("name"));
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, "目录名称不能为空");
        }
        Integer parentId = intOrNull(data.get("parent_id"));
        if (DEFAULT_DIRECTORY_NAME.equals(name) && parentId == null) {
            throw new VideoBusinessException(400, "「默认分组」为系统保留名称，请使用其他目录名");
        }
        if (parentId != null && directoryRepository.findById(parentId).isEmpty()) {
            throw new VideoBusinessException(400, "父目录不存在");
        }
        DeviceDirectoryRow row = new DeviceDirectoryRow();
        row.setName(name);
        row.setParentId(parentId);
        row.setDescription(str(data.get("description")));
        row.setSortOrder(intOr(data.get("sort_order"), 0));
        int id = directoryRepository.insert(row);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", id);
        result.put("name", name);
        result.put("parent_id", parentId);
        result.put("description", row.getDescription());
        result.put("sort_order", row.getSortOrder());
        return result;
    }

    public Map<String, Object> updateDirectory(int directoryId, Map<String, Object> data) {
        DeviceDirectoryRow directory = directoryRepository.findById(directoryId)
                .orElseThrow(() -> new VideoBusinessException(400, "目录不存在: ID=" + directoryId));
        if (isDefaultDirectory(directory)) {
            if (data.containsKey("name") && !directory.getName().equals(str(data.get("name")))) {
                throw new VideoBusinessException(400, "默认分组不可重命名");
            }
            if (data.containsKey("parent_id") && !sameParent(directory.getParentId(), data.get("parent_id"))) {
                throw new VideoBusinessException(400, "默认分组不可移动");
            }
        }
        if (data.containsKey("name")) {
            String name = str(data.get("name"));
            if (name.isEmpty()) {
                throw new VideoBusinessException(400, "目录名称不能为空");
            }
            directory.setName(name);
        }
        if (data.containsKey("parent_id")) {
            Integer parentId = intOrNull(data.get("parent_id"));
            if (parentId != null && parentId == directoryId) {
                throw new VideoBusinessException(400, "不能将目录设置为自己的子目录");
            }
            if (parentId != null && directoryRepository.findById(parentId).isEmpty()) {
                throw new VideoBusinessException(400, "父目录不存在");
            }
            directory.setParentId(parentId);
        }
        if (data.containsKey("description")) {
            directory.setDescription(str(data.get("description")));
        }
        if (data.containsKey("sort_order")) {
            directory.setSortOrder(intOr(data.get("sort_order"), 0));
        }
        if (data.containsKey("snap_save_time")) {
            directory.setSnapSaveTime(intOr(data.get("snap_save_time"), 1));
        }
        if (data.containsKey("record_save_time")) {
            directory.setRecordSaveTime(intOr(data.get("record_save_time"), 1));
        }
        directoryRepository.update(directory);
        if (data.containsKey("snap_save_time") || data.containsKey("record_save_time")) {
            int cascaded = deviceSpaceSyncService.propagateDirectorySaveTime(
                    directoryId,
                    data.containsKey("snap_save_time") ? directory.getSnapSaveTime() : null,
                    data.containsKey("record_save_time") ? directory.getRecordSaveTime() : null
            );
            if (cascaded > 0) {
                log.info("目录 {} 保存时间级联更新 {} 个空间", directoryId, cascaded);
            }
        }
        Map<String, Object> result = directoryToMap(directory);
        result.put("snap_save_time", directory.getSnapSaveTime());
        result.put("record_save_time", directory.getRecordSaveTime());
        return result;
    }

    public void deleteDirectory(int directoryId) {
        DeviceDirectoryRow directory = directoryRepository.findById(directoryId)
                .orElseThrow(() -> new VideoBusinessException(400, "目录不存在: ID=" + directoryId));
        if (isDefaultDirectory(directory)) {
            throw new VideoBusinessException(400, "默认分组不可删除");
        }
        long children = directoryRepository.countChildren(directoryId);
        if (children > 0) {
            throw new VideoBusinessException(400,
                    "不能删除当前目录，存在 " + children + " 个下级目录。请先删除所有下级目录后，才可以删除当前目录");
        }
        long devices = directoryRepository.countDevices(directoryId);
        if (devices > 0) {
            throw new VideoBusinessException(400, "该目录下存在 " + devices + " 个设备，请先移除设备后再删除目录");
        }
        directoryRepository.delete(directoryId);
    }

    public Map<String, Object> listDirectoryDevices(int directoryId, int pageNo, int pageSize, String search) {
        DeviceDirectoryRow directory = directoryRepository.findById(directoryId)
                .orElseThrow(() -> new VideoBusinessException(400, "目录不存在: ID=" + directoryId));
        if (isDefaultDirectory(directory)) {
            try {
                gb28181SyncService.syncFromWvp(false, null, null);
            } catch (Exception e) {
                log.warn("目录设备列表前国标同步失败: {}", e.getMessage());
            }
        }
        if (pageNo < 1 || pageSize < 1) {
            throw new VideoBusinessException(400, "参数错误：pageNo和pageSize必须为正整数");
        }
        List<Map<String, Object>> items = deviceRepository.listByDirectory(directoryId, pageNo, pageSize, search).stream()
                .map(cameraService::toDeviceMap)
                .toList();
        for (Map<String, Object> item : items) {
            Object deviceId = item.get("id");
            if (deviceId != null) {
                deviceSpaceSyncService.ensureDeviceSpaces(String.valueOf(deviceId));
            }
        }
        return Map.of("items", items, "total", deviceRepository.countByDirectory(directoryId, search));
    }

    public Map<String, Object> moveDeviceToDirectory(String deviceId, Integer directoryId) {
        DeviceRow device = deviceRepository.findById(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备不存在: ID=" + deviceId));
        int targetDir;
        if (directoryId == null || directoryId == 0) {
            targetDir = directoryRepository.ensureDefaultDirectory();
        } else {
            if (directoryRepository.findById(directoryId).isEmpty()) {
                throw new VideoBusinessException(400, "目录不存在");
            }
            targetDir = directoryId;
        }
        deviceRepository.updateDirectoryId(deviceId, targetDir);
        deviceSpaceSyncService.syncDeviceSpacesToDirectory(deviceId, targetDir);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("device_id", deviceId);
        data.put("directory_id", targetDir);
        return data;
    }

    public void validateDirectoryJson(Object data) {
        if (data == null) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        directoryJsonSyncService.validateTree(directoryJsonSyncService.parsePayload(data));
    }

    public void syncDirectoryJson(Object data) {
        if (data == null) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        directoryJsonSyncService.syncFromJson(directoryJsonSyncService.parsePayload(data));
    }

    public SyncGb28181Result syncGb28181(
            Map<String, Object> body,
            String authorization,
            String xAuthorization
    ) {
        Map<String, Object> payload = body != null ? body : Map.of();
        if (payload.containsKey("data") && payload.get("data") instanceof Map<?, ?> inner
                && ((Map<?, ?>) inner).containsKey("channels")) {
            @SuppressWarnings("unchecked")
            Map<String, Object> nested = (Map<String, Object>) inner;
            payload = nested;
        }

        Object channelsObj = payload.get("channels");
        Map<String, Object> stats;
        if (channelsObj instanceof List<?> channels && !channels.isEmpty()) {
            stats = gb28181SyncService.syncFromPayload(channels, true);
        } else {
            stats = gb28181SyncService.syncFromWvp(true, authorization, xAuthorization);
        }
        try {
            gb28181SyncService.backfillAiStreamUrls();
        } catch (Exception ignored) {
            // mirrors Python warning-only backfill
        }
        String message = gb28181SyncService.buildSyncMessage(stats);
        Map<String, Object> data = gb28181SyncService.buildSyncResponse(stats);
        return new SyncGb28181Result(message, data);
    }

    public record SyncGb28181Result(String message, Map<String, Object> data) {
    }

    private List<Map<String, Object>> buildTree(Integer parentId) {
        List<DeviceDirectoryRow> directories = directoryRepository.findByParentId(parentId);
        List<Map<String, Object>> result = new ArrayList<>();
        for (DeviceDirectoryRow directory : directories) {
            Map<String, Object> node = directoryToMap(directory);
            node.put("is_default", isDefaultDirectory(directory));
            node.put("device_count", directoryRepository.countDevices(directory.getId()));
            node.put("children", buildTree(directory.getId()));
            result.add(node);
        }
        return result;
    }

    private List<Map<String, Object>> buildMonitorTree(Integer parentId) {
        List<DeviceDirectoryRow> directories = directoryRepository.findByParentId(parentId);
        List<Map<String, Object>> result = new ArrayList<>();
        for (DeviceDirectoryRow directory : directories) {
            List<DeviceRow> devices = deviceRepository.listByDirectoryId(directory.getId());
            Map<String, Object> node = new LinkedHashMap<>();
            node.put("type", "directory");
            node.put("id", directory.getId());
            node.put("name", directory.getName());
            node.put("parent_id", directory.getParentId());
            node.put("sort_order", directory.getSortOrder());
            node.put("snap_save_time", directory.getSnapSaveTime());
            node.put("record_save_time", directory.getRecordSaveTime());
            node.put("is_default", isDefaultDirectory(directory));
            node.put("device_count", devices.size());
            node.put("children", buildMonitorTree(directory.getId()));
            node.put("devices", devices.stream().map(this::monitorDeviceNode).toList());
            result.add(node);
        }
        return result;
    }

    private Map<String, Object> monitorDeviceNode(DeviceRow device) {
        Map<String, Object> d = cameraService.toDeviceMap(device);
        Map<String, Object> node = new LinkedHashMap<>();
        node.put("type", "device");
        node.put("id", d.get("id"));
        node.put("name", d.get("name"));
        node.put("http_stream", d.get("http_stream"));
        node.put("rtmp_stream", d.get("rtmp_stream"));
        node.put("ai_http_stream", d.get("ai_http_stream"));
        node.put("ai_rtmp_stream", d.get("ai_rtmp_stream"));
        node.put("online", d.get("online"));
        node.put("directory_id", d.get("directory_id"));
        node.put("device_kind", d.get("device_kind"));
        node.put("source", d.get("source"));
        node.put("nvr_id", d.get("nvr_id"));
        node.put("nvr_channel", d.get("nvr_channel"));
        node.put("nvr_label", d.get("nvr_label"));
        return node;
    }

    private Map<String, Object> directoryToMap(DeviceDirectoryRow directory) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", directory.getId());
        map.put("name", directory.getName());
        map.put("parent_id", directory.getParentId());
        map.put("description", directory.getDescription());
        map.put("sort_order", directory.getSortOrder());
        map.put("snap_save_time", directory.getSnapSaveTime());
        map.put("record_save_time", directory.getRecordSaveTime());
        map.put("created_at", directory.getCreatedAt() != null
                ? ISO_INSTANT.format(directory.getCreatedAt().atOffset(ZoneOffset.UTC)) : null);
        map.put("updated_at", directory.getUpdatedAt() != null
                ? ISO_INSTANT.format(directory.getUpdatedAt().atOffset(ZoneOffset.UTC)) : null);
        return map;
    }

    private boolean isDefaultDirectory(DeviceDirectoryRow directory) {
        return directory != null
                && DEFAULT_DIRECTORY_NAME.equals(directory.getName())
                && directory.getParentId() == null;
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }

    private static Integer intOrNull(Object value) {
        if (value == null || "".equals(String.valueOf(value))) {
            return null;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static int intOr(Object value, int defaultValue) {
        if (value == null || "".equals(String.valueOf(value))) {
            return defaultValue;
        }
        return Integer.parseInt(String.valueOf(value));
    }

    private static boolean sameParent(Integer current, Object requested) {
        Integer req = intOrNull(requested);
        if (current == null && req == null) {
            return true;
        }
        return current != null && current.equals(req);
    }
}
