package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.CameraService;
import com.basiclab.iot.video.service.ViewForwardService;
import com.basiclab.iot.video.service.camera.CameraAdminService;
import com.basiclab.iot.video.service.camera.CameraConflictService;
import com.basiclab.iot.video.service.camera.CameraDirectoryService;
import com.basiclab.iot.video.service.camera.CameraFlighthubService;
import com.basiclab.iot.video.service.camera.CameraHardwareService;
import com.basiclab.iot.video.service.camera.CameraLocationService;
import com.basiclab.iot.video.service.camera.CameraNvrService;
import com.basiclab.iot.video.service.camera.CameraStreamTicketService;
import com.basiclab.iot.video.service.camera.CameraTrackService;
import com.basiclab.iot.video.service.media.CameraPublishCallbackService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/camera")
@RequiredArgsConstructor
public class CameraController {

    private final CameraService cameraService;
    private final ViewForwardService viewForwardService;
    private final CameraAdminService cameraAdminService;
    private final CameraLocationService cameraLocationService;
    private final CameraTrackService cameraTrackService;
    private final CameraDirectoryService cameraDirectoryService;
    private final CameraNvrService cameraNvrService;
    private final CameraHardwareService cameraHardwareService;
    private final CameraFlighthubService cameraFlighthubService;
    private final CameraStreamTicketService cameraStreamTicketService;
    private final CameraConflictService cameraConflictService;
    private final CameraPublishCallbackService cameraPublishCallbackService;

    @PostMapping("/stream/ticket/sign")
    public ResponseEntity<VideoApiResponse<Map<String, Object>>> signStreamTicket(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @RequestHeader(value = "X-Authorization", required = false) String xAuthorization,
            @RequestHeader(value = "tenant-id", required = false) String tenantId,
            @RequestHeader(value = "Tenant-Id", required = false) String tenantIdAlt,
            @RequestBody(required = false) Map<String, Object> body) {
        String auth = authorization != null && !authorization.isBlank() ? authorization : xAuthorization;
        String tenant = tenantId != null && !tenantId.isBlank() ? tenantId : tenantIdAlt;
        Map<String, Object> result = cameraStreamTicketService.signTicket(auth, tenant, body != null ? body : Map.of());
        int httpStatus = ((Number) result.get("httpStatus")).intValue();
        int code = ((Number) result.get("code")).intValue();
        String msg = String.valueOf(result.get("msg"));
        if (httpStatus == 401) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(VideoApiResponse.error(code, msg));
        }
        if (httpStatus != 200) {
            return ResponseEntity.status(HttpStatus.valueOf(httpStatus)).body(VideoApiResponse.error(code, msg));
        }
        @SuppressWarnings("unchecked")
        Map<String, Object> data = (Map<String, Object>) result.get("data");
        return ResponseEntity.ok(VideoApiResponse.success(msg, data));
    }

    @PostMapping("/device/{deviceId}/stream/start")
    public VideoApiResponse<Map<String, Object>> startStream(@PathVariable String deviceId) {
        Map<String, Object> result = viewForwardService.startStream(deviceId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @PostMapping("/device/{deviceId}/stream/stop")
    public VideoApiResponse<Map<String, Object>> stopStream(@PathVariable String deviceId) {
        Map<String, Object> result = viewForwardService.stopStream(deviceId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @GetMapping("/device/{deviceId}/stream/status")
    public VideoApiResponse<Map<String, Object>> streamStatus(@PathVariable String deviceId) {
        return VideoApiResponse.success(viewForwardService.streamStatus(deviceId));
    }

    @GetMapping("/list")
    public VideoApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search) {
        Map<String, Object> result = cameraService.listDevices(pageNo, pageSize, search);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) result.get("items");
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        Object total = result.get("total");
        if (total instanceof Number number) {
            response.setTotal(number.intValue());
        }
        return response;
    }

    @GetMapping("/locations")
    public VideoApiResponse<List<Map<String, Object>>> listLocations(
            @RequestParam(required = false) Integer directory_id,
            @RequestParam(defaultValue = "true") String has_location) {
        boolean hasLocationOnly = !"false".equalsIgnoreCase(has_location) && !"0".equals(has_location) && !"no".equalsIgnoreCase(has_location);
        List<Map<String, Object>> items = cameraLocationService.listLocations(directory_id, hasLocationOnly);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        response.setTotal(items.size());
        return response;
    }

    @GetMapping("/device/{deviceId}/location")
    public VideoApiResponse<Map<String, Object>> getDeviceLocation(@PathVariable String deviceId) {
        return VideoApiResponse.success(cameraLocationService.getLocation(deviceId));
    }

    @PutMapping("/device/{deviceId}/location")
    public VideoApiResponse<Map<String, Object>> updateDeviceLocation(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> body) {
        return VideoApiResponse.success("位置更新成功", cameraLocationService.updateLocation(deviceId, body));
    }

    @PostMapping("/locations/batch")
    public VideoApiResponse<Map<String, Object>> batchUpdateLocations(@RequestBody Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = body.get("items") instanceof List<?> list
                ? (List<Map<String, Object>>) list
                : body.get("locations") instanceof List<?> list2 ? (List<Map<String, Object>>) list2 : List.of();
        return VideoApiResponse.success(cameraLocationService.batchUpdateLocations(items));
    }

    @GetMapping("/tracks/sessions")
    public VideoApiResponse<List<Map<String, Object>>> listTrackSessions(
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String begin_datetime,
            @RequestParam(required = false) String begin,
            @RequestParam(required = false) String end_datetime,
            @RequestParam(required = false) String end,
            @RequestParam(defaultValue = "50") int limit) {
        String beginValue = begin_datetime != null ? begin_datetime : begin;
        String endValue = end_datetime != null ? end_datetime : end;
        List<Map<String, Object>> items = cameraTrackService.listSessions(device_id, beginValue, endValue, limit);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        response.setTotal(items.size());
        return response;
    }

    @GetMapping("/tracks/points")
    public VideoApiResponse<List<Map<String, Object>>> listTrackPoints(
            @RequestParam(required = false) Long session_id,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String begin_datetime,
            @RequestParam(required = false) String begin,
            @RequestParam(required = false) String end_datetime,
            @RequestParam(required = false) String end,
            @RequestParam(defaultValue = "5000") int limit) {
        String beginValue = begin_datetime != null ? begin_datetime : begin;
        String endValue = end_datetime != null ? end_datetime : end;
        List<Map<String, Object>> items = cameraTrackService.listPoints(session_id, device_id, beginValue, endValue, limit);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        response.setTotal(items.size());
        return response;
    }

    @GetMapping("/device/{deviceId}")
    public VideoApiResponse<Map<String, Object>> get(@PathVariable String deviceId) {
        return VideoApiResponse.success(cameraService.getDevice(deviceId));
    }

    @GetMapping("/device/{deviceId}/inference-input")
    public VideoApiResponse<Map<String, Object>> inferenceInput(@PathVariable String deviceId) {
        return VideoApiResponse.success(cameraAdminService.resolveInferenceInput(deviceId));
    }

    @PostMapping("/device/{deviceId}/ensure-spaces")
    public VideoApiResponse<Map<String, Object>> ensureSpaces(@PathVariable String deviceId) {
        return VideoApiResponse.success("存储空间已就绪", cameraAdminService.ensureSpaces(deviceId));
    }

    @PostMapping("/register/device")
    public VideoApiResponse<Map<String, Object>> registerDevice(@RequestBody Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        String deviceId = cameraAdminService.registerDevice(body);
        return VideoApiResponse.success("设备注册成功", Map.of("id", deviceId));
    }

    @GetMapping("/flighthub/config")
    public VideoApiResponse<Map<String, Object>> flighthubConfig() {
        return VideoApiResponse.success(cameraFlighthubService.publicConfig());
    }

    @PostMapping("/register/device/dji-live")
    public VideoApiResponse<Map<String, Object>> registerDjiLive(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("success", cameraFlighthubService.registerDjiLive(body != null ? body : Map.of()));
    }

    @PostMapping("/flighthub/live-stream/start")
    public VideoApiResponse<Object> startFlighthubLive(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> result = cameraFlighthubService.startLiveStream(body != null ? body : Map.of());
        if (!Boolean.TRUE.equals(result.get("ok"))) {
            return VideoApiResponse.error(
                    ((Number) result.getOrDefault("code", 500)).intValue(),
                    String.valueOf(result.get("msg"))
            );
        }
        return VideoApiResponse.success("success", result.get("data"));
    }

    @PostMapping("/flighthub/live-stream/refresh-device/{deviceId}")
    public VideoApiResponse<Object> refreshFlighthubLive(
            @PathVariable String deviceId,
            @RequestBody(required = false) Map<String, Object> body) {
        return startFlighthubLive(cameraFlighthubService.refreshLiveByDevice(deviceId, body != null ? body : Map.of()));
    }

    @PostMapping("/register/device/onvif")
    public VideoApiResponse<Map<String, Object>> registerByOnvif(@RequestBody Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        String ip = String.valueOf(body.getOrDefault("ip", "")).trim();
        int port = Integer.parseInt(String.valueOf(body.getOrDefault("port", 80)));
        String password = String.valueOf(body.getOrDefault("password", "")).trim();
        String username = body.get("username") != null ? String.valueOf(body.get("username")).trim() : null;
        String deviceId = cameraAdminService.registerByOnvif(ip, port, password, username);
        return VideoApiResponse.success("设备注册成功", Map.of("id", deviceId));
    }

    @PutMapping("/device/{deviceId}")
    public VideoApiResponse<Void> updateDevice(@PathVariable String deviceId, @RequestBody Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            throw new VideoBusinessException(400, "请求数据不能为空");
        }
        cameraAdminService.updateDevice(deviceId, body);
        return VideoApiResponse.success("设备信息更新成功", null);
    }

    @DeleteMapping("/device/{deviceId}")
    public VideoApiResponse<Void> deleteDevice(@PathVariable String deviceId) {
        cameraAdminService.deleteDevice(deviceId);
        return VideoApiResponse.success("设备删除成功", null);
    }

    @PostMapping("/devices/batch-delete")
    public VideoApiResponse<Map<String, Object>> batchDeleteDevices(@RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> data = body != null ? body : Map.of();
        @SuppressWarnings("unchecked")
        List<Object> deviceIds = data.get("device_ids") instanceof List<?> list
                ? (List<Object>) list
                : data.get("deviceIds") instanceof List<?> list2 ? (List<Object>) list2 : List.of();
        if (deviceIds.isEmpty()) {
            throw new VideoBusinessException(400, "device_ids 不能为空");
        }
        return VideoApiResponse.success("批量删除完成", cameraAdminService.batchDelete(deviceIds));
    }

    @PostMapping("/device/{deviceId}/ptz")
    public ResponseEntity<Map<String, Object>> controlPtz(
            @PathVariable String deviceId,
            @RequestBody(required = false) Map<String, Object> body) {
        try {
            cameraHardwareService.ptz(deviceId, body);
            Map<String, Object> ok = new LinkedHashMap<>();
            ok.put("success", true);
            ok.put("message", "PTZ command executed");
            return ResponseEntity.ok(ok);
        } catch (VideoBusinessException ex) {
            Map<String, Object> err = new LinkedHashMap<>();
            err.put("error", ex.getCode() == 400 ? "Camera not found" : "Internal server error");
            return ResponseEntity.status(ex.getCode() == 400 ? HttpStatus.BAD_REQUEST : HttpStatus.INTERNAL_SERVER_ERROR).body(err);
        }
    }

    @PostMapping("/device/{deviceId}/rtsp/start")
    public VideoApiResponse<Map<String, Object>> startRtspCapture(
            @PathVariable String deviceId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("RTSP截图任务已启动", cameraHardwareService.startRtspCapture(deviceId, body));
    }

    @PostMapping("/device/{deviceId}/rtsp/stop")
    public VideoApiResponse<Void> stopRtspCapture(@PathVariable String deviceId) {
        cameraHardwareService.stopRtspCapture(deviceId);
        return VideoApiResponse.success("RTSP截图任务已停止", null);
    }

    @GetMapping("/device/{deviceId}/rtsp/status")
    public VideoApiResponse<Map<String, Object>> rtspStatus(@PathVariable String deviceId) {
        return VideoApiResponse.success(Map.of("status", cameraHardwareService.rtspStatus(deviceId)));
    }

    @PostMapping("/device/{deviceId}/onvif/start")
    public VideoApiResponse<Map<String, Object>> startOnvifCapture(
            @PathVariable String deviceId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("ONVIF截图任务已启动", cameraHardwareService.startOnvifCapture(deviceId, body));
    }

    @PostMapping("/device/{deviceId}/onvif/stop")
    public VideoApiResponse<Void> stopOnvifCapture(@PathVariable String deviceId) {
        cameraHardwareService.stopOnvifCapture(deviceId);
        return VideoApiResponse.success("ONVIF截图任务已停止", null);
    }

    @GetMapping("/device/{deviceId}/onvif/status")
    public VideoApiResponse<Map<String, Object>> onvifStatus(@PathVariable String deviceId) {
        return VideoApiResponse.success(Map.of("status", cameraHardwareService.onvifStatus(deviceId)));
    }

    @GetMapping("/device/{deviceId}/onvif/presets")
    public VideoApiResponse<List<Map<String, Object>>> listOnvifPresets(@PathVariable String deviceId) {
        return VideoApiResponse.success(cameraHardwareService.listOnvifPresets(deviceId));
    }

    @PostMapping("/device/{deviceId}/onvif/presets")
    public VideoApiResponse<Map<String, Object>> setOnvifPreset(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> body) {
        String name = String.valueOf(body.getOrDefault("name", "")).trim();
        if (name.isEmpty()) {
            throw new VideoBusinessException(400, "预置点名称不能为空");
        }
        String presetToken = body.get("preset_token") != null ? String.valueOf(body.get("preset_token")).trim() : null;
        return VideoApiResponse.success("预置点已保存", cameraHardwareService.setOnvifPreset(deviceId, name, presetToken));
    }

    @PostMapping("/device/{deviceId}/onvif/presets/call")
    public VideoApiResponse<Void> callOnvifPreset(@PathVariable String deviceId, @RequestBody Map<String, Object> body) {
        String presetToken = String.valueOf(body.getOrDefault("preset_token", body.getOrDefault("token", ""))).trim();
        if (presetToken.isEmpty()) {
            throw new VideoBusinessException(400, "缺少 preset_token");
        }
        cameraHardwareService.callOnvifPreset(deviceId, presetToken);
        return VideoApiResponse.success("预置点已调用", null);
    }

    @DeleteMapping("/device/{deviceId}/onvif/presets/{presetToken}")
    public VideoApiResponse<Void> deleteOnvifPreset(
            @PathVariable String deviceId,
            @PathVariable String presetToken) {
        cameraHardwareService.deleteOnvifPreset(deviceId, presetToken);
        return VideoApiResponse.success("预置点已删除", null);
    }

    @PostMapping("/device/{deviceId}/snapshot")
    public VideoApiResponse<Map<String, Object>> captureSnapshot(@PathVariable String deviceId) {
        try {
            return VideoApiResponse.success("抓拍成功", cameraHardwareService.captureSnapshot(deviceId));
        } catch (VideoBusinessException ex) {
            if (ex.getCode() == 500) {
                return VideoApiResponse.error(ex.getCode(), ex.getMessage());
            }
            throw ex;
        }
    }

    @GetMapping("/nvr/list")
    public VideoApiResponse<List<Map<String, Object>>> listNvrs(
            @RequestParam(required = false, defaultValue = "false") String include_cameras) {
        boolean include = "1".equals(include_cameras) || "true".equalsIgnoreCase(include_cameras);
        return VideoApiResponse.success(cameraNvrService.listNvrs(include));
    }

    @GetMapping("/nvr/{nvrId}")
    public VideoApiResponse<Map<String, Object>> getNvr(
            @PathVariable int nvrId,
            @RequestParam(defaultValue = "true") String include_cameras) {
        boolean include = !"false".equalsIgnoreCase(include_cameras) && !"0".equals(include_cameras);
        return VideoApiResponse.success(cameraNvrService.getNvr(nvrId, include));
    }

    @PostMapping("/nvr/upsert")
    public VideoApiResponse<Map<String, Object>> upsertNvr(@RequestBody Map<String, Object> body) {
        return VideoApiResponse.success("success", cameraNvrService.upsertNvr(body != null ? body : Map.of()));
    }

    @PostMapping("/nvr/register-channels")
    public VideoApiResponse<Map<String, Object>> registerNvrChannels(@RequestBody Map<String, Object> body) {
        try {
            return VideoApiResponse.success("success", cameraNvrService.registerChannels(body));
        } catch (VideoBusinessException ex) {
            throw ex;
        }
    }

    @DeleteMapping("/nvr/{nvrId}")
    public VideoApiResponse<Void> deleteNvr(@PathVariable int nvrId) {
        cameraNvrService.deleteNvr(nvrId);
        return VideoApiResponse.success("success", null);
    }

    @PostMapping("/nvr/batch-delete")
    public VideoApiResponse<Map<String, Object>> batchDeleteNvrs(@RequestBody(required = false) Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<Object> nvrIds = body != null && body.get("nvr_ids") instanceof List<?> list
                ? (List<Object>) list
                : body != null && body.get("nvrIds") instanceof List<?> list2 ? (List<Object>) list2 : List.of();
        if (nvrIds.isEmpty()) {
            throw new VideoBusinessException(400, "nvr_ids 不能为空");
        }
        return VideoApiResponse.success("批量删除完成", cameraNvrService.batchDelete(nvrIds));
    }

    @PostMapping("/scan/segment")
    public VideoApiResponse<List<Map<String, Object>>> scanSegment(@RequestBody Map<String, Object> body) {
        return VideoApiResponse.success(cameraHardwareService.scanSegment(body));
    }

    @PostMapping("/scan/nvr/channels")
    public VideoApiResponse<Map<String, Object>> scanNvrChannels(@RequestBody Map<String, Object> body) {
        return VideoApiResponse.success(cameraHardwareService.scanNvrChannels(body));
    }

    @GetMapping("/discovery")
    public VideoApiResponse<List<Map<String, Object>>> discovery() {
        return VideoApiResponse.success(cameraHardwareService.discoverDevices());
    }

    @PostMapping("/refresh")
    public VideoApiResponse<Void> refresh() {
        cameraHardwareService.refreshDevices();
        return VideoApiResponse.success("设备刷新任务已启动", null);
    }

    @PostMapping("/callback/on_publish")
    public VideoApiResponse<Void> onPublish(@RequestBody(required = false) Map<String, Object> body) {
        cameraPublishCallbackService.handleOnPublish(body);
        VideoApiResponse<Void> response = new VideoApiResponse<>();
        response.setCode(0);
        response.setMsg(null);
        response.setMessage(null);
        return response;
    }

    @PostMapping("/callback/on_dvr")
    public VideoApiResponse<Void> onDvr(@RequestBody(required = false) Map<String, Object> body) {
        VideoApiResponse<Void> response = new VideoApiResponse<>();
        response.setCode(0);
        response.setMsg(null);
        response.setMessage(null);
        return response;
    }

    @GetMapping("/directory/list")
    public VideoApiResponse<List<Map<String, Object>>> listDirectories() {
        return VideoApiResponse.success(cameraDirectoryService.listTree());
    }

    @GetMapping("/directory/monitor-tree")
    public VideoApiResponse<Map<String, Object>> monitorTree(
            @RequestParam(defaultValue = "1") String skip_sync,
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @RequestHeader(value = "X-Authorization", required = false) String xAuthorization) {
        boolean skip = !"false".equalsIgnoreCase(skip_sync) && !"0".equals(skip_sync);
        return VideoApiResponse.success(
                cameraDirectoryService.monitorTree(skip, authorization, xAuthorization)
        );
    }

    @PostMapping("/directory/validate-json")
    public VideoApiResponse<Void> validateDirectoryJson(@RequestBody Object body) {
        cameraDirectoryService.validateDirectoryJson(body);
        return VideoApiResponse.success("校验通过", null);
    }

    @PostMapping("/directory/sync-json")
    public VideoApiResponse<Void> syncDirectoryJson(@RequestBody Object body) {
        cameraDirectoryService.syncDirectoryJson(body);
        return VideoApiResponse.success("目录同步成功", null);
    }

    @PostMapping("/directory/sync-gb28181")
    public VideoApiResponse<Map<String, Object>> syncGb28181(
            @RequestBody(required = false) Map<String, Object> body,
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @RequestHeader(value = "X-Authorization", required = false) String xAuthorization) {
        CameraDirectoryService.SyncGb28181Result result = cameraDirectoryService.syncGb28181(
                body != null ? body : Map.of(),
                authorization,
                xAuthorization
        );
        return VideoApiResponse.success(result.message(), result.data());
    }

    @PostMapping("/directory")
    public VideoApiResponse<Map<String, Object>> createDirectory(@RequestBody Map<String, Object> body) {
        return VideoApiResponse.success("目录创建成功", cameraDirectoryService.createDirectory(body));
    }

    @PutMapping("/directory/{directoryId}")
    public VideoApiResponse<Map<String, Object>> updateDirectory(
            @PathVariable int directoryId,
            @RequestBody Map<String, Object> body) {
        return VideoApiResponse.success("目录更新成功", cameraDirectoryService.updateDirectory(directoryId, body));
    }

    @DeleteMapping("/directory/{directoryId}")
    public VideoApiResponse<Void> deleteDirectory(@PathVariable int directoryId) {
        cameraDirectoryService.deleteDirectory(directoryId);
        return VideoApiResponse.success("目录删除成功", null);
    }

    @GetMapping("/directory/{directoryId}/devices")
    public VideoApiResponse<List<Map<String, Object>>> listDirectoryDevices(
            @PathVariable int directoryId,
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search) {
        Map<String, Object> result = cameraDirectoryService.listDirectoryDevices(directoryId, pageNo, pageSize, search);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) result.get("items");
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        response.setTotal(((Number) result.get("total")).intValue());
        return response;
    }

    @PutMapping("/device/{deviceId}/directory")
    public VideoApiResponse<Map<String, Object>> moveDeviceToDirectory(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> body) {
        if (!body.containsKey("directory_id")) {
            throw new VideoBusinessException(400, "directory_id参数不能为空");
        }
        Integer directoryId = body.get("directory_id") == null ? null : Integer.parseInt(String.valueOf(body.get("directory_id")));
        return VideoApiResponse.success("设备移动成功", cameraDirectoryService.moveDeviceToDirectory(deviceId, directoryId));
    }

    @GetMapping("/directory/{directoryId}")
    public VideoApiResponse<Map<String, Object>> getDirectory(@PathVariable int directoryId) {
        return VideoApiResponse.success(cameraDirectoryService.getDirectory(directoryId));
    }

    @GetMapping("/device/conflicts")
    public VideoApiResponse<List<String>> deviceConflicts(@RequestParam(required = false) String task_type) {
        return VideoApiResponse.success(cameraConflictService.listConflicts(task_type));
    }
}
