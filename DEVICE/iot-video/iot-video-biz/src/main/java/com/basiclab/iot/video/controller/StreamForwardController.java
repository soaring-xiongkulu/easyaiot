package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.StreamForwardTaskRow;
import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.StreamForwardAdminService;
import com.basiclab.iot.video.service.StreamForwardLogService;
import com.basiclab.iot.video.service.StreamForwardService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/stream-forward")
@RequiredArgsConstructor
public class StreamForwardController {

    private final StreamForwardService streamForwardService;
    private final StreamForwardAdminService adminService;
    private final StreamForwardLogService logService;

    @GetMapping("/task/list")
    public VideoApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String is_enabled) {
        Boolean enabled = null;
        if (is_enabled != null && !is_enabled.isBlank()) {
            enabled = "1".equals(is_enabled) || Boolean.parseBoolean(is_enabled);
        }
        Map<String, Object> result = adminService.listTasks(pageNo, pageSize, search, device_id, enabled);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) result.get("items");
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        Object total = result.get("total");
        if (total instanceof Number number) {
            response.setTotal(number.intValue());
        }
        return response;
    }

    @GetMapping("/task/{taskId}")
    public VideoApiResponse<Map<String, Object>> getTask(@PathVariable long taskId) {
        return VideoApiResponse.success(streamForwardService.getTask(taskId));
    }

    @PostMapping("/task")
    public VideoApiResponse<Map<String, Object>> create(@RequestBody Map<String, Object> body) {
        StreamForwardTaskRow task = adminService.create(body);
        return VideoApiResponse.success("创建成功", task.toMap());
    }

    @PutMapping("/task/{taskId}")
    public VideoApiResponse<Map<String, Object>> update(
            @PathVariable long taskId,
            @RequestBody Map<String, Object> body) {
        Map<String, Object> result = adminService.update(taskId, body);
        @SuppressWarnings("unchecked")
        Map<String, Object> data = (Map<String, Object>) result.get("task");
        Object syncAction = result.get("sync_action");
        if (syncAction != null) {
            data = new LinkedHashMap<>(data);
            data.put("sync_action", syncAction);
        }
        return VideoApiResponse.success("更新成功", data);
    }

    @DeleteMapping("/task/{taskId}")
    public VideoApiResponse<Void> delete(@PathVariable long taskId) {
        adminService.delete(taskId);
        return VideoApiResponse.success("删除成功", null);
    }

    @PostMapping("/task/{taskId}/start")
    public VideoApiResponse<Map<String, Object>> start(@PathVariable long taskId) {
        Map<String, Object> result = streamForwardService.start(taskId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @PostMapping("/task/{taskId}/stop")
    public VideoApiResponse<Map<String, Object>> stop(@PathVariable long taskId) {
        Map<String, Object> result = streamForwardService.stop(taskId);
        return VideoApiResponse.success(
                String.valueOf(result.get("message")),
                (Map<String, Object>) result.get("data")
        );
    }

    @PostMapping("/task/{taskId}/restart")
    public VideoApiResponse<Map<String, Object>> restart(@PathVariable long taskId) {
        Map<String, Object> result = streamForwardService.restart(taskId);
        return VideoApiResponse.success(
                "重启成功",
                (Map<String, Object>) result.get("data")
        );
    }

    @PostMapping("/heartbeat")
    public VideoApiResponse<Map<String, Object>> heartbeat(@RequestBody Map<String, Object> body) {
        Map<String, Object> data = streamForwardService.receiveHeartbeat(body);
        return VideoApiResponse.success("心跳接收成功", data);
    }

    @GetMapping("/task/{taskId}/status")
    public VideoApiResponse<Map<String, Object>> status(@PathVariable long taskId) {
        return VideoApiResponse.success(streamForwardService.taskStatus(taskId));
    }

    @GetMapping("/task/{taskId}/logs")
    public VideoApiResponse<Map<String, Object>> logs(
            @PathVariable long taskId,
            @RequestParam(defaultValue = "100") int lines,
            @RequestParam(required = false) String date) {
        return VideoApiResponse.success(logService.getTaskLogs(taskId, lines, date));
    }

    @GetMapping("/task/{taskId}/streams")
    public VideoApiResponse<List<Map<String, Object>>> streams(@PathVariable long taskId) {
        return VideoApiResponse.success(adminService.listStreams(taskId));
    }

    @PostMapping("/device/{deviceId}/ensure-task")
    public VideoApiResponse<Map<String, Object>> ensureDeviceTask(@PathVariable String deviceId) {
        Map<String, Object> data = adminService.ensureDeviceTask(deviceId);
        return VideoApiResponse.success("推流转发任务已确保存在", data);
    }
}
