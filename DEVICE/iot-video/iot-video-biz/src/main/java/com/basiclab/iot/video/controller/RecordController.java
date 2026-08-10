package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.SpaceListApiResponse;
import com.basiclab.iot.video.service.RecordSpaceService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/record")
@RequiredArgsConstructor
public class RecordController {

    private final RecordSpaceService recordSpaceService;

    @GetMapping("/space/list")
    public SpaceListApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize) {
        Map<String, Object> result = recordSpaceService.listSpaces(pageNo, pageSize);
        return spaceListResponse(result);
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
