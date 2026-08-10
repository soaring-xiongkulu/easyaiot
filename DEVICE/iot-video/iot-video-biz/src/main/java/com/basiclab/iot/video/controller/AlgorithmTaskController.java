package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.AlgorithmTaskRow;
import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.AlgorithmTaskAdminService;
import com.basiclab.iot.video.service.AlgorithmTaskLifecycleService;
import com.basiclab.iot.video.service.AlgorithmTaskLogService;
import com.basiclab.iot.video.service.PostProcessEnqueueAudit;
import com.basiclab.iot.video.service.PostProcessService;
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

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/algorithm")
@RequiredArgsConstructor
public class AlgorithmTaskController {

    private final AlgorithmTaskLifecycleService lifecycleService;
    private final AlgorithmTaskAdminService adminService;
    private final AlgorithmTaskLogService logService;
    private final PostProcessService postProcessService;

    @GetMapping("/task/list")
    public VideoApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String task_type,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String is_enabled) {
        Boolean enabled = null;
        if (is_enabled != null && !is_enabled.isBlank()) {
            enabled = "1".equals(is_enabled) || Boolean.parseBoolean(is_enabled);
        }
        Map<String, Object> result = lifecycleService.listTasks(pageNo, pageSize, search, task_type, device_id, enabled);
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) result.get("items");
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(items);
        Object total = result.get("total");
        if (total instanceof Number number) {
            response.setTotal(number.intValue());
        }
        return response;
    }

    @GetMapping("/task/{id}")
    public VideoApiResponse<Map<String, Object>> detail(@PathVariable("id") long id) {
        return VideoApiResponse.success(lifecycleService.getTask(id));
    }

    @PostMapping("/task")
    public VideoApiResponse<Map<String, Object>> create(@RequestBody Map<String, Object> body) {
        AlgorithmTaskRow task = adminService.create(body);
        return VideoApiResponse.success("创建成功", task.toMap());
    }

    @PutMapping("/task/{id}")
    public VideoApiResponse<Map<String, Object>> update(
            @PathVariable("id") long id,
            @RequestBody Map<String, Object> body) {
        AlgorithmTaskRow task = adminService.update(id, body);
        return VideoApiResponse.success("更新成功", task.toMap());
    }

    @DeleteMapping("/task/{id}")
    public VideoApiResponse<Void> delete(@PathVariable("id") long id) {
        adminService.delete(id);
        return VideoApiResponse.success("删除成功", null);
    }

    @GetMapping("/task/{id}/services/status")
    public VideoApiResponse<Map<String, Object>> servicesStatus(@PathVariable("id") long id) {
        return VideoApiResponse.success(lifecycleService.getServicesStatus(id));
    }

    @PostMapping("/task/{id}/start")
    public VideoApiResponse<Map<String, Object>> start(@PathVariable("id") long id) {
        Map<String, Object> result = lifecycleService.start(id);
        return VideoApiResponse.success(String.valueOf(result.get("message")), (Map<String, Object>) result.get("data"));
    }

    @PostMapping("/task/{id}/stop")
    public VideoApiResponse<Map<String, Object>> stop(@PathVariable("id") long id) {
        Map<String, Object> result = lifecycleService.stop(id);
        return VideoApiResponse.success(String.valueOf(result.get("message")), (Map<String, Object>) result.get("data"));
    }

    @PostMapping("/task/{id}/restart")
    public VideoApiResponse<Map<String, Object>> restart(@PathVariable("id") long id) {
        Map<String, Object> result = lifecycleService.restart(id);
        return VideoApiResponse.success("重启成功", (Map<String, Object>) result.get("data"));
    }

    @GetMapping("/task/{id}/extractor/logs")
    public VideoApiResponse<Map<String, Object>> extractorLogs(
            @PathVariable("id") long id,
            @RequestParam(defaultValue = "100") int lines,
            @RequestParam(required = false) String date) {
        return VideoApiResponse.success(logService.getExtractorLogs(id, lines, date));
    }

    @GetMapping("/task/{id}/sorter/logs")
    public VideoApiResponse<Map<String, Object>> sorterLogs(
            @PathVariable("id") long id,
            @RequestParam(defaultValue = "100") int lines,
            @RequestParam(required = false) String date) {
        return VideoApiResponse.success(logService.getSorterLogs(id, lines, date));
    }

    @GetMapping("/task/{id}/pusher/logs")
    public VideoApiResponse<Map<String, Object>> pusherLogs(
            @PathVariable("id") long id,
            @RequestParam(defaultValue = "100") int lines,
            @RequestParam(required = false) String date) {
        return VideoApiResponse.success(logService.getPusherLogs(id, lines, date));
    }

    @GetMapping("/task/{id}/realtime/logs")
    public VideoApiResponse<Map<String, Object>> realtimeLogs(
            @PathVariable("id") long id,
            @RequestParam(defaultValue = "100") int lines,
            @RequestParam(required = false) String date) {
        return VideoApiResponse.success(logService.getRealtimeLogs(id, lines, date));
    }

    @GetMapping("/task/{id}/streams")
    public VideoApiResponse<List<Map<String, Object>>> streams(@PathVariable("id") long id) {
        return VideoApiResponse.success(adminService.listStreams(id));
    }

    @GetMapping("/task/{id}/post-process/status")
    public VideoApiResponse<Map<String, Object>> postProcessStatus(
            @PathVariable("id") long id,
            @RequestParam(name = "reset_audit", required = false) Boolean resetAudit) {
        if (Boolean.TRUE.equals(resetAudit)) {
            PostProcessEnqueueAudit.reset();
        }
        return VideoApiResponse.success(postProcessService.getStatus(id));
    }

    @PostMapping("/task/{id}/post-process/init")
    public VideoApiResponse<Map<String, Object>> postProcessInit(@PathVariable("id") long id) {
        return VideoApiResponse.success(postProcessService.initWorkspace(id));
    }

    @GetMapping("/task/{id}/post-process/ide-url")
    public VideoApiResponse<Map<String, Object>> postProcessIdeUrl(@PathVariable("id") long id) {
        return VideoApiResponse.success(postProcessService.getIdeUrl(id));
    }

    @PutMapping("/task/{id}/post-process/toggle")
    public VideoApiResponse<Map<String, Object>> postProcessToggle(
            @PathVariable("id") long id,
            @RequestBody Map<String, Object> body) {
        return VideoApiResponse.success(postProcessService.toggle(id, body));
    }

    @GetMapping("/task/{id}/post-process/results")
    public Map<String, Object> postProcessResults(
            @PathVariable("id") long id,
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String begin_datetime,
            @RequestParam(required = false) String end_datetime) {
        LocalDateTime begin = parseDateTime(begin_datetime);
        LocalDateTime end = parseDateTime(end_datetime);
        Map<String, Object> result = postProcessService.listResults(id, pageNo, pageSize, device_id, begin, end);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("code", 0);
        response.put("msg", "success");
        response.putAll(result);
        return response;
    }

    private static LocalDateTime parseDateTime(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        String text = raw.trim().replace("Z", "");
        if (text.contains("+")) {
            text = text.substring(0, text.indexOf('+'));
        }
        return LocalDateTime.parse(text, DateTimeFormatter.ISO_LOCAL_DATE_TIME);
    }
}
