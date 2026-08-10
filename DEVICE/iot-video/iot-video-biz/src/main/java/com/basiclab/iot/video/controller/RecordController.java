package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.SpaceListApiResponse;
import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.record.RecordSpaceAdminService;
import com.basiclab.iot.video.service.record.RecordVideoService;
import com.basiclab.iot.video.support.MediaPathSupport;
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

import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/record")
@RequiredArgsConstructor
public class RecordController {

    private final RecordSpaceAdminService recordSpaceAdminService;
    private final RecordVideoService recordVideoService;

    @GetMapping("/space/list")
    public SpaceListApiResponse<List<Map<String, Object>>> listSpaces(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "root") String parentKey,
            @RequestParam(required = false) String scope) {
        Map<String, Object> result = recordSpaceAdminService.listSpaces(pageNo, pageSize, search, parentKey, scope);
        return spaceListResponse(result);
    }

    @GetMapping("/space/{spaceId}")
    public VideoApiResponse<Map<String, Object>> getSpace(@PathVariable int spaceId) {
        return VideoApiResponse.success(recordSpaceAdminService.getSpace(spaceId));
    }

    @GetMapping("/space/device/{deviceId}")
    public VideoApiResponse<Map<String, Object>> getSpaceByDevice(@PathVariable String deviceId) {
        return VideoApiResponse.success(recordSpaceAdminService.getSpaceByDevice(deviceId));
    }

    @PostMapping("/space")
    public ResponseEntity<VideoApiResponse<Void>> createSpace(@RequestBody(required = false) Map<String, Object> body) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(VideoApiResponse.error(
                403, "监控录像空间不能手动创建，系统会在创建设备时自动创建监控录像空间"));
    }

    @PutMapping("/space/{spaceId}")
    public VideoApiResponse<Map<String, Object>> updateSpace(
            @PathVariable int spaceId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("监控录像空间更新成功",
                recordSpaceAdminService.updateSpace(spaceId, body != null ? body : Map.of()));
    }

    @PutMapping("/space/group-policy")
    public VideoApiResponse<Map<String, Object>> updateGroupPolicy(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> data = recordSpaceAdminService.updateGroupPolicy(body != null ? body : Map.of());
        int updated = ((Number) data.get("updated_count")).intValue();
        return VideoApiResponse.success("分组存储策略已更新，已同步 " + updated + " 个非自定义设备空间", data);
    }

    @DeleteMapping("/space/{spaceId}")
    public VideoApiResponse<Void> deleteSpace(@PathVariable int spaceId) {
        recordSpaceAdminService.deleteSpace(spaceId);
        return VideoApiResponse.success("监控录像空间删除成功", null);
    }

    @PostMapping("/space/sync/minio")
    public VideoApiResponse<Map<String, Object>> syncSpacesMinio() {
        return VideoApiResponse.success("同步完成", recordSpaceAdminService.syncSpacesToMinio());
    }

    @GetMapping("/space/{spaceId}/videos/dates")
    public VideoApiResponse<List<String>> listVideoDates(
            @PathVariable int spaceId, @RequestParam(required = false) String device_id) {
        return VideoApiResponse.success(recordVideoService.listDates(spaceId, device_id));
    }

    @GetMapping("/space/{spaceId}/videos/day")
    public VideoApiResponse<Map<String, Object>> listVideosByDay(
            @PathVariable int spaceId,
            @RequestParam(required = false) String date,
            @RequestParam(required = false) String device_id) {
        return VideoApiResponse.success(recordVideoService.listDayDetail(spaceId, date, device_id));
    }

    @GetMapping("/space/device/{deviceId}/resolve-alert")
    public VideoApiResponse<Map<String, Object>> resolveAlertSegment(
            @PathVariable String deviceId,
            @RequestParam(required = false) String alert_id,
            @RequestParam(required = false) String alertId) {
        String aid = alert_id != null && !alert_id.isBlank() ? alert_id : alertId;
        if (aid == null || aid.isBlank()) {
            throw new com.basiclab.iot.video.exception.VideoBusinessException(400, "alert_id 参数不能为空");
        }
        return VideoApiResponse.success(recordVideoService.resolveAlertSegment(deviceId, Integer.parseInt(aid)));
    }

    @GetMapping("/space/{spaceId}/videos")
    public VideoApiResponse<List<Map<String, Object>>> listVideos(
            @PathVariable int spaceId,
            @RequestParam(required = false) String device_id,
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        Map<String, Object> result = recordVideoService.listVideos(spaceId, device_id, pageNo, pageSize, search, startTime, endTime);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success((List<Map<String, Object>>) result.get("items"));
        response.setTotal(((Number) result.get("total")).intValue());
        return response;
    }

    @GetMapping("/space/{spaceId}/video/**")
    public ResponseEntity<?> getVideo(@PathVariable int spaceId, HttpServletRequest request) {
        String objectName = MediaPathSupport.pathWithinHandlerMapping(request);
        try {
            byte[] content = recordVideoService.getVideoContent(spaceId, objectName);
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(recordVideoService.videoContentType(objectName)))
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + recordVideoService.videoFilename(objectName) + "\"")
                    .body(content);
        } catch (VideoBusinessException ex) {
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(VideoApiResponse.error(ex.getCode(), ex.getMessage()));
        }
    }

    @DeleteMapping("/space/{spaceId}/videos")
    public VideoApiResponse<Map<String, Object>> deleteVideos(
            @PathVariable int spaceId, @RequestBody(required = false) Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<String> names = body != null ? (List<String>) body.get("object_names") : null;
        return VideoApiResponse.success("删除成功", recordVideoService.deleteVideos(spaceId, names));
    }

    @PostMapping("/space/{spaceId}/videos/sync")
    public VideoApiResponse<Map<String, Object>> syncVideos(@PathVariable int spaceId) {
        return VideoApiResponse.success("同步完成", recordVideoService.syncMetadata(spaceId));
    }

    @PostMapping("/space/{spaceId}/videos/cleanup")
    public VideoApiResponse<Map<String, Object>> cleanupVideos(
            @PathVariable int spaceId, @RequestBody(required = false) Map<String, Object> body) {
        if (body == null || !body.containsKey("save_time_hours")) {
            throw new com.basiclab.iot.video.exception.VideoBusinessException(400, "请求数据不能为空，需要提供 save_time_hours 参数");
        }
        int hours = ((Number) body.get("save_time_hours")).intValue();
        return VideoApiResponse.success("清理完成", recordVideoService.cleanup(spaceId, hours));
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
