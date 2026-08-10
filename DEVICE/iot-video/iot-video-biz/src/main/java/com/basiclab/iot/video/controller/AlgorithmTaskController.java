package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.AlgorithmTaskLifecycleService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/algorithm")
@RequiredArgsConstructor
public class AlgorithmTaskController {

    private final AlgorithmTaskLifecycleService lifecycleService;

    @GetMapping("/task/list")
    public VideoApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search) {
        Map<String, Object> result = lifecycleService.listTasks(pageNo, pageSize, search);
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
}
