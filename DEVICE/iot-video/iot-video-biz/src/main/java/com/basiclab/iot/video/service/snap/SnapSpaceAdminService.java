package com.basiclab.iot.video.service.snap;

import com.basiclab.iot.video.dal.SnapSpaceRepository;
import com.basiclab.iot.video.dal.SnapImageRepository;
import com.basiclab.iot.video.dal.SnapTaskRepository;
import com.basiclab.iot.video.dal.SpaceGroupPolicyRepository;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.support.SpaceNodeSupport;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class SnapSpaceAdminService {

    private final SnapSpaceRepository snapSpaceRepository;
    private final SnapTaskRepository snapTaskRepository;
    private final SnapImageRepository snapImageRepository;
    private final SpaceGroupPolicyRepository groupPolicyRepository;

    public Map<String, Object> listSpaces(int pageNo, int pageSize, String search, String parentKey, String scope) {
        List<Map<String, Object>> items = snapSpaceRepository.listRootNodes(pageNo, pageSize);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("items", items);
        result.put("total", snapSpaceRepository.count());
        result.put("parent_key", parentKey != null && !parentKey.isBlank() ? parentKey : "root");
        result.put("breadcrumbs", SpaceNodeSupport.rootBreadcrumbs());
        result.put("is_search", search != null && !search.isBlank());
        result.put("scope", scope);
        return result;
    }

    public Map<String, Object> getSpace(int spaceId) {
        return snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
    }

    public Map<String, Object> getSpaceByDevice(String deviceId) {
        return snapSpaceRepository.findByDeviceId(deviceId)
                .orElseThrow(() -> new VideoBusinessException(400, "设备 " + deviceId + " 没有关联的抓拍空间"));
    }

    public Map<String, Object> updateSpace(int spaceId, Map<String, Object> data) {
        snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
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
        snapSpaceRepository.updateFields(spaceId, fields);
        return getSpace(spaceId);
    }

    public void deleteSpace(int spaceId) {
        snapSpaceRepository.findById(spaceId)
                .orElseThrow(() -> new VideoBusinessException(400, "抓拍空间不存在: ID=" + spaceId));
        long tasks = snapTaskRepository.countBySpaceId(spaceId);
        if (tasks > 0) {
            throw new VideoBusinessException(400, "该空间下还有 " + tasks + " 个任务，请先删除任务");
        }
        long images = snapImageRepository.countBySpaceId(spaceId);
        if (images > 0) {
            throw new VideoBusinessException(400, "该空间下还有 " + images + " 张抓拍图片，请先删除所有图片后再删除空间");
        }
        snapSpaceRepository.delete(spaceId);
    }

    public Map<String, Object> updateGroupPolicy(Map<String, Object> data) {
        String groupType = String.valueOf(data.getOrDefault("group_type", "")).trim().toLowerCase();
        String groupKey = String.valueOf(data.getOrDefault("group_key", "")).trim();
        Object saveTimeObj = data.get("save_time");
        if (saveTimeObj == null) {
            throw new VideoBusinessException(400, "save_time 不能为空");
        }
        int saveTime = saveTimeObj instanceof Number n ? n.intValue() : Integer.parseInt(String.valueOf(saveTimeObj));
        groupPolicyRepository.upsertSnapSaveTime(groupType, groupKey, saveTime);
        int updated = groupPolicyRepository.syncNonCustomSnapSpaces(groupType, groupKey, saveTime);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("group_type", groupType);
        result.put("group_key", groupKey);
        result.put("save_time", saveTime);
        result.put("updated_count", updated);
        return result;
    }

    public Map<String, Object> syncSpacesToMinio() {
        int total = snapSpaceRepository.listAllSpaces().size();
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total", total);
        result.put("synced", total);
        result.put("skipped", 0);
        result.put("message", "mini 形态跳过 MinIO 同步，仅校验数据库空间记录");
        return result;
    }
}
