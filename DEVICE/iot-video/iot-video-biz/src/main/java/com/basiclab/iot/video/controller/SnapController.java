package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.SpaceListApiResponse;
import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.SnapSpaceService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
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

    private final SnapSpaceService snapSpaceService;

    @GetMapping("/space/list")
    public SpaceListApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize) {
        Map<String, Object> result = snapSpaceService.listSpaces(pageNo, pageSize);
        return spaceListResponse(result);
    }

    @PostMapping("/space")
    public ResponseEntity<VideoApiResponse<Void>> createSpace(@RequestBody(required = false) Map<String, Object> body) {
        VideoApiResponse<Void> response = VideoApiResponse.error(
                403,
                "抓拍空间不能手动创建，系统会在创建设备时自动创建抓拍空间"
        );
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
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
