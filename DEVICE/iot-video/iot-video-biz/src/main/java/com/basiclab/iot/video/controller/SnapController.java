package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.SpaceListApiResponse;
import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.snap.SnapAlgorithmService;
import com.basiclab.iot.video.service.snap.SnapImageService;
import com.basiclab.iot.video.service.snap.SnapRegionService;
import com.basiclab.iot.video.service.snap.SnapSpaceAdminService;
import com.basiclab.iot.video.service.snap.SnapStorageService;
import com.basiclab.iot.video.service.snap.SnapTaskService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/snap")
@RequiredArgsConstructor
public class SnapController {

    private final SnapSpaceAdminService snapSpaceAdminService;
    private final SnapTaskService snapTaskService;
    private final SnapRegionService snapRegionService;
    private final SnapAlgorithmService snapAlgorithmService;
    private final SnapStorageService snapStorageService;
    private final SnapImageService snapImageService;

    @GetMapping("/space/list")
    public SpaceListApiResponse<List<Map<String, Object>>> listSpaces(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "root") String parentKey,
            @RequestParam(required = false) String scope) {
        Map<String, Object> result = snapSpaceAdminService.listSpaces(pageNo, pageSize, search, parentKey, scope);
        return spaceListResponse(result);
    }

    @GetMapping("/space/{spaceId}")
    public VideoApiResponse<Map<String, Object>> getSpace(@PathVariable int spaceId) {
        return VideoApiResponse.success(snapSpaceAdminService.getSpace(spaceId));
    }

    @GetMapping("/space/device/{deviceId}")
    public VideoApiResponse<Map<String, Object>> getSpaceByDevice(@PathVariable String deviceId) {
        return VideoApiResponse.success(snapSpaceAdminService.getSpaceByDevice(deviceId));
    }

    @PostMapping("/space")
    public ResponseEntity<VideoApiResponse<Void>> createSpace(@RequestBody(required = false) Map<String, Object> body) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(VideoApiResponse.error(
                403, "抓拍空间不能手动创建，系统会在创建设备时自动创建抓拍空间"));
    }

    @PutMapping("/space/{spaceId}")
    public VideoApiResponse<Map<String, Object>> updateSpace(
            @PathVariable int spaceId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("抓拍空间更新成功", snapSpaceAdminService.updateSpace(spaceId, body != null ? body : Map.of()));
    }

    @PutMapping("/space/group-policy")
    public VideoApiResponse<Map<String, Object>> updateGroupPolicy(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> data = snapSpaceAdminService.updateGroupPolicy(body != null ? body : Map.of());
        int updated = ((Number) data.get("updated_count")).intValue();
        return VideoApiResponse.success("分组存储策略已更新，已同步 " + updated + " 个非自定义设备空间", data);
    }

    @DeleteMapping("/space/{spaceId}")
    public VideoApiResponse<Void> deleteSpace(@PathVariable int spaceId) {
        snapSpaceAdminService.deleteSpace(spaceId);
        return VideoApiResponse.success("抓拍空间删除成功", null);
    }

    @PostMapping("/space/sync/minio")
    public VideoApiResponse<Map<String, Object>> syncSpacesMinio() {
        return VideoApiResponse.success("同步完成", snapSpaceAdminService.syncSpacesToMinio());
    }

    @GetMapping("/task/list")
    public VideoApiResponse<List<Map<String, Object>>> listTasks(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) Integer space_id,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) Integer status) {
        Map<String, Object> result = snapTaskService.list(pageNo, pageSize, space_id, device_id, search, status);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success((List<Map<String, Object>>) result.get("items"));
        response.setTotal(((Number) result.get("total")).intValue());
        return response;
    }

    @GetMapping("/task/{taskId}")
    public VideoApiResponse<Map<String, Object>> getTask(@PathVariable int taskId) {
        return VideoApiResponse.success(snapTaskService.get(taskId));
    }

    @PostMapping("/task")
    public VideoApiResponse<Map<String, Object>> createTask(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("抓拍任务创建成功", snapTaskService.create(body != null ? body : Map.of()));
    }

    @PutMapping("/task/{taskId}")
    public VideoApiResponse<Map<String, Object>> updateTask(
            @PathVariable int taskId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("抓拍任务更新成功", snapTaskService.update(taskId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/task/{taskId}")
    public VideoApiResponse<Void> deleteTask(@PathVariable int taskId) {
        snapTaskService.delete(taskId);
        return VideoApiResponse.success("抓拍任务删除成功", null);
    }

    @PostMapping("/task/{taskId}/start")
    public VideoApiResponse<Map<String, Object>> startTask(@PathVariable int taskId) {
        return VideoApiResponse.success("任务已启动", snapTaskService.start(taskId));
    }

    @PostMapping("/task/{taskId}/stop")
    public VideoApiResponse<Map<String, Object>> stopTask(@PathVariable int taskId) {
        return VideoApiResponse.success("任务已停止", snapTaskService.stop(taskId));
    }

    @PostMapping("/task/{taskId}/restart")
    public VideoApiResponse<Map<String, Object>> restartTask(@PathVariable int taskId) {
        return VideoApiResponse.success("任务已重启", snapTaskService.restart(taskId));
    }

    @GetMapping("/task/{taskId}/logs")
    public VideoApiResponse<List<Map<String, Object>>> taskLogs(
            @PathVariable int taskId,
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "50") int pageSize,
            @RequestParam(required = false) String level) {
        Map<String, Object> result = snapTaskService.logs(taskId, pageNo, pageSize, level);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success((List<Map<String, Object>>) result.get("logs"));
        response.setTotal(((Number) result.get("total")).intValue());
        return response;
    }

    @GetMapping("/task/{taskId}/regions")
    public VideoApiResponse<List<Map<String, Object>>> listRegions(@PathVariable int taskId) {
        return VideoApiResponse.success(snapRegionService.listByTask(taskId));
    }

    @GetMapping("/region/{regionId}")
    public VideoApiResponse<Map<String, Object>> getRegion(@PathVariable int regionId) {
        return VideoApiResponse.success(snapRegionService.get(regionId));
    }

    @PostMapping("/region")
    public VideoApiResponse<Map<String, Object>> createRegion(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("检测区域创建成功", snapRegionService.create(body != null ? body : Map.of()));
    }

    @PutMapping("/region/{regionId}")
    public VideoApiResponse<Map<String, Object>> updateRegion(
            @PathVariable int regionId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("检测区域更新成功", snapRegionService.update(regionId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/region/{regionId}")
    public VideoApiResponse<Void> deleteRegion(@PathVariable int regionId) {
        snapRegionService.delete(regionId);
        return VideoApiResponse.success("检测区域删除成功", null);
    }

    @GetMapping("/task/{taskId}/services")
    public VideoApiResponse<List<Map<String, Object>>> listTaskServices(@PathVariable int taskId) {
        return VideoApiResponse.success(snapAlgorithmService.listTaskServices(taskId));
    }

    @PostMapping("/task/{taskId}/service")
    public VideoApiResponse<Map<String, Object>> createTaskService(
            @PathVariable int taskId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("算法服务配置创建成功",
                snapAlgorithmService.createTaskService(taskId, body != null ? body : Map.of()));
    }

    @PutMapping("/service/{serviceId}")
    public VideoApiResponse<Map<String, Object>> updateTaskService(
            @PathVariable int serviceId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("算法服务配置更新成功",
                snapAlgorithmService.updateTaskService(serviceId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/service/{serviceId}")
    public VideoApiResponse<Void> deleteTaskService(@PathVariable int serviceId) {
        snapAlgorithmService.deleteTaskService(serviceId);
        return VideoApiResponse.success("算法服务配置删除成功", null);
    }

    @GetMapping("/region/{regionId}/services")
    public VideoApiResponse<List<Map<String, Object>>> listRegionServices(@PathVariable int regionId) {
        return VideoApiResponse.success(snapAlgorithmService.listRegionServices(regionId));
    }

    @PostMapping("/region/{regionId}/service")
    public VideoApiResponse<Map<String, Object>> createRegionService(
            @PathVariable int regionId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("区域算法服务配置创建成功",
                snapAlgorithmService.createRegionService(regionId, body != null ? body : Map.of()));
    }

    @PutMapping("/region-service/{serviceId}")
    public VideoApiResponse<Map<String, Object>> updateRegionService(
            @PathVariable int serviceId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("区域算法服务配置更新成功",
                snapAlgorithmService.updateRegionService(serviceId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/region-service/{serviceId}")
    public VideoApiResponse<Void> deleteRegionService(@PathVariable int serviceId) {
        snapAlgorithmService.deleteRegionService(serviceId);
        return VideoApiResponse.success("区域算法服务配置删除成功", null);
    }

    @GetMapping("/device/{deviceId}/storage")
    public VideoApiResponse<Map<String, Object>> getDeviceStorage(@PathVariable String deviceId) {
        return VideoApiResponse.success(snapStorageService.getOrCreate(deviceId));
    }

    @PutMapping("/device/{deviceId}/storage")
    public VideoApiResponse<Map<String, Object>> updateDeviceStorage(
            @PathVariable String deviceId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("设备存储配置更新成功",
                snapStorageService.update(deviceId, body != null ? body : Map.of()));
    }

    @PostMapping("/device/{deviceId}/storage/cleanup")
    public VideoApiResponse<Map<String, Object>> cleanupDeviceStorage(@PathVariable String deviceId) {
        return VideoApiResponse.success("存储清理完成", snapStorageService.cleanup(deviceId));
    }

    @GetMapping("/space/{spaceId}/images")
    public VideoApiResponse<List<Map<String, Object>>> listImages(
            @PathVariable int spaceId,
            @RequestParam(required = false) String device_id,
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String source,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        Map<String, Object> result = snapImageService.list(spaceId, device_id, pageNo, pageSize, search, source, startTime, endTime);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success((List<Map<String, Object>>) result.get("items"));
        response.setTotal(((Number) result.get("total")).intValue());
        return response;
    }

    @GetMapping("/space/{spaceId}/image/{*objectName}")
    public ResponseEntity<byte[]> getImage(@PathVariable int spaceId, @PathVariable String objectName) {
        byte[] content = snapImageService.getImageContent(spaceId, objectName);
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(snapImageService.imageContentType(objectName)))
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "inline; filename=\"" + snapImageService.imageFilename(objectName) + "\"")
                .body(content);
    }

    @DeleteMapping("/space/{spaceId}/images")
    public VideoApiResponse<Map<String, Object>> deleteImages(
            @PathVariable int spaceId, @RequestBody(required = false) Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<String> names = body != null ? (List<String>) body.get("object_names") : null;
        return VideoApiResponse.success("删除完成", snapImageService.deleteImages(spaceId, names));
    }

    @PostMapping("/space/{spaceId}/images/sync")
    public VideoApiResponse<Map<String, Object>> syncImages(@PathVariable int spaceId) {
        return VideoApiResponse.success("同步完成", snapImageService.syncMetadata(spaceId));
    }

    @PostMapping("/space/{spaceId}/images/cleanup")
    public VideoApiResponse<Map<String, Object>> cleanupImages(
            @PathVariable int spaceId, @RequestBody(required = false) Map<String, Object> body) {
        if (body == null || !body.containsKey("save_time_hours")) {
            throw new com.basiclab.iot.video.exception.VideoBusinessException(400, "需要提供 save_time_hours 参数");
        }
        int hours = ((Number) body.get("save_time_hours")).intValue();
        return VideoApiResponse.success("清理完成", snapImageService.cleanup(spaceId, hours));
    }

    @SuppressWarnings("unchecked")
    private SpaceListApiResponse<List<Map<String, Object>>> spaceListResponse(Map<String, Object> result) {
        int total = ((Number) result.get("total")).intValue();
        return SpaceListApiResponse.success(
                (List<Map<String, Object>>) result.get("items"),
                total,
                String.valueOf(result.get("parent_key")),
                (List<Map<String, Object>>) result.get("breadcrumbs"),
                Boolean.TRUE.equals(result.get("is_search")),
                (String) result.get("scope")
        );
    }
}
