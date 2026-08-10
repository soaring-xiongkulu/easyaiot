package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.AlertService;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/video/alert")
@RequiredArgsConstructor
public class AlertController {

    private final AlertService alertService;

    @GetMapping("/page")
    public VideoApiResponse<Map<String, Object>> page(@RequestParam Map<String, String> params) {
        return VideoApiResponse.success(alertService.getPage(params));
    }

    @GetMapping("/correlation")
    public VideoApiResponse<Map<String, Object>> correlation(
            @RequestParam(required = false) String correlation_id,
            @RequestParam(required = false) String correlationId) {
        String cid = correlation_id != null && !correlation_id.isBlank() ? correlation_id : correlationId;
        return VideoApiResponse.success(alertService.getCorrelationEvents(cid));
    }

    @GetMapping("/count")
    public VideoApiResponse<Map<String, Object>> count(@RequestParam Map<String, String> params) {
        return VideoApiResponse.success(alertService.getCount(params));
    }

    @GetMapping("/statistics")
    public VideoApiResponse<Map<String, Object>> statistics() {
        return VideoApiResponse.success(alertService.getDashboardStatistics());
    }

    @GetMapping("/image")
    public Object image(@RequestParam(required = false) String path) {
        try {
            Path file = alertService.resolveLocalImagePath(path);
            Resource resource = new FileSystemResource(file);
            String contentType = Files.probeContentType(file);
            if (contentType == null) {
                contentType = "image/jpeg";
            }
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header(HttpHeaders.CONTENT_DISPOSITION,
                            "inline; filename=\"" + file.getFileName() + "\"")
                    .body(resource);
        } catch (VideoBusinessException ex) {
            return VideoApiResponse.error(ex.getCode(), ex.getMessage());
        } catch (Exception ex) {
            return VideoApiResponse.error(500, "获取失败: " + ex.getMessage());
        }
    }

    @GetMapping("/record")
    public Object record(@RequestParam(required = false) String path) {
        try {
            String decoded = path != null ? java.net.URLDecoder.decode(path, java.nio.charset.StandardCharsets.UTF_8).trim() : "";
            if (decoded.isEmpty()) {
                return recordError(HttpStatus.BAD_REQUEST, 400, "路径参数不能为空");
            }
            Path file = alertService.resolveLocalRecordPath(decoded);
            Resource resource = new FileSystemResource(file);
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(alertService.recordMimetype(file)))
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline")
                    .body(resource);
        } catch (VideoBusinessException ex) {
            HttpStatus status = ex.getCode() == 404 ? HttpStatus.NOT_FOUND : HttpStatus.BAD_REQUEST;
            return recordError(status, ex.getCode(), ex.getMessage());
        } catch (Exception ex) {
            return recordError(HttpStatus.INTERNAL_SERVER_ERROR, 500, "获取失败: " + ex.getMessage());
        }
    }

    @GetMapping("/record/query")
    public Object queryRecord(
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String alert_time,
            @RequestParam(required = false) String alert_id,
            @RequestParam(defaultValue = "300") int time_range) {
        try {
            Map<String, Object> result = alertService.queryAlertRecord(device_id, alert_time, alert_id, time_range);
            Object code = result.get("code");
            if (code instanceof Number n && n.intValue() != 0) {
                return ResponseEntity.ok(result);
            }
            if (result.containsKey("data") && result.get("data") instanceof Map<?, ?> data) {
                return VideoApiResponse.success("success", data);
            }
            return result;
        } catch (VideoBusinessException ex) {
            return VideoApiResponse.error(ex.getCode(), ex.getMessage());
        } catch (Exception ex) {
            return VideoApiResponse.error(500, "查询失败: " + ex.getMessage());
        }
    }

    @DeleteMapping("/clear")
    public VideoApiResponse<Map<String, Object>> clear(@RequestParam(required = false) String task_name) {
        return VideoApiResponse.success("success", alertService.clearByTaskName(task_name));
    }

    @DeleteMapping("/clear/all")
    public VideoApiResponse<Map<String, Object>> clearAll() {
        return VideoApiResponse.success("success", alertService.clearAll());
    }

    private static ResponseEntity<Map<String, Object>> recordError(HttpStatus status, int code, String message) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("code", code);
        body.put("message", message);
        body.put("data", null);
        return ResponseEntity.status(status).body(body);
    }

}
