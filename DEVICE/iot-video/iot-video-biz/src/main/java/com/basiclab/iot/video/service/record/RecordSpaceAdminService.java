package com.basiclab.iot.video.service.record;

import com.basiclab.iot.video.dal.RecordSpaceRepository;
import com.basiclab.iot.video.dal.RecordFileRepository;
import com.basiclab.iot.video.dal.SpaceGroupPolicyRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.minio.VideoMinioService;
import com.basiclab.iot.video.support.SpaceNodeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class RecordSpaceAdminService {

    private final RecordSpaceRepository recordSpaceRepository;
    private final RecordFileRepository recordFileRepository;
    private final SpaceGroupPolicyRepository groupPolicyRepository;
    private final VideoMinioService videoMinioService;

    public Map<String, Object> listSpaces(int pageNo, int pageSize, String search, String parentKey, String scope) {
        List<Map<String, Object>> all = recordSpaceRepository.listRootNodes(1, Integer.MAX_VALUE);
        List<Map<String, Object>> items = SpaceNodeSupport.paginate(all, pageNo, pageSize);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", items);
        result.put("total", all.size());
        result.put("parent_key", parentKey != null && !parentKey.isBlank() ? parentKey : "root");
        result.put("breadcrumbs", SpaceNodeSupport.rootBreadcrumbs());
        result.put("is_search", search != null && !search.isBlank());
        result.put("scope", scope);
        return result;
    }

    public Map<String, Object> getSpace(int spaceId) {
        return recordSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "监控录像空间不存在: ID=" + spaceId));
    }

    public Map<String, Object> getSpaceByDevice(String deviceId) {
        return recordSpaceRepository.findByDeviceId(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备 " + deviceId + " 没有关联的监控录像空间"));
    }

    public Map<String, Object> updateSpace(int spaceId, Map<String, Object> data) {
        recordSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "监控录像空间不存在: ID=" + spaceId));
        Map<String, Object> fields = new LinkedHashMap<>();
        if (data.containsKey("space_name")) {
            fields.put("space_name", String.valueOf(data.get("space_name")).trim());
        }
        if (data.containsKey("save_mode")) {
            fields.put("save_mode", data.get("save_mode"));
        }
        if (data.containsKey("save_time")) {
            fields.put("save_time", data.get("save_time"));
        }
        if (data.containsKey("save_time_custom")) {
            fields.put("save_time_custom", data.get("save_time_custom"));
        }
        if (data.containsKey("description")) {
            fields.put("description", String.valueOf(data.get("description")).trim());
        }
        recordSpaceRepository.updateFields(spaceId, fields);
        return getSpace(spaceId);
    }

    public void deleteSpace(int spaceId) {
        Map<String, Object> space = recordSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "监控录像空间不存在: ID=" + spaceId));
        long videos = recordFileRepository.count(spaceId, stringField(space.get("device_id")), null, null, null);
        if (videos > 0) {
            throw new VideoBusinessException(400, "该空间下还有 " + videos + " 个监控录像，请先删除所有录像后再删除空间");
        }
        String bucketName = space.get("bucket_name") != null
                ? String.valueOf(space.get("bucket_name"))
                : videoMinioService.recordBucket();
        String deviceId = space.get("device_id") != null ? String.valueOf(space.get("device_id")) : null;
        videoMinioService.deleteDevicePrefix(bucketName, deviceId);
        recordSpaceRepository.delete(spaceId);
    }

    public Map<String, Object> updateGroupPolicy(Map<String, Object> data) {
        String groupType = String.valueOf(data.getOrDefault("group_type", "")).trim().toLowerCase();
        String groupKey = String.valueOf(data.getOrDefault("group_key", "")).trim();
        Object saveTimeObj = data.get("save_time");
        if (saveTimeObj == null) {
            throw new VideoBusinessException(400, "save_time 不能为空");
        }
        int saveTime = saveTimeObj instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(saveTimeObj));
        groupPolicyRepository.upsertRecordSaveTime(groupType, groupKey, saveTime);
        int updated = groupPolicyRepository.syncNonCustomRecordSpaces(groupType, groupKey, saveTime);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("group_type", groupType);
        result.put("group_key", groupKey);
        result.put("save_time", saveTime);
        result.put("updated_count", updated);
        return result;
    }

    public Map<String, Object> syncSpacesToMinio() {
        List<Map<String, Object>> spaces = recordSpaceRepository.listAllSpaces();
        return videoMinioService.syncDeviceDirectories(videoMinioService.recordBucket(), spaces, true);
    }

    private static String stringField(Object value) {
        return value == null ? "" : String.valueOf(value).trim();
    }
}
