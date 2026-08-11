package com.basiclab.iot.sink.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.sink.service.media.DvrUploadService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * SRS/ZLM DVR Hook（录像上传 MinIO + Playback/告警回填），替代 VIDEO dvr_upload_service。
 */
@Slf4j
@Tag(name = "媒体 Hook")
@RestController
@RequestMapping("/media/hook")
@RequiredArgsConstructor
public class MediaHookController {

    private final DvrUploadService dvrUploadService;

    @PostMapping("/srs/on_dvr")
    @Operation(summary = "SRS DVR 回调：从 NFS 读录像并上传 MinIO")
    public Map<String, Object> srsOnDvr(@RequestBody Map<String, Object> body) {
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", 0);
        try {
            boolean ok = dvrUploadService.processDvrEvent(body);
            resp.put("msg", ok ? "success" : "skipped_or_failed");
        } catch (Exception e) {
            log.error("SRS on_dvr 处理失败: {}", e.getMessage(), e);
            resp.put("code", -1);
            resp.put("msg", e.getMessage());
        }
        return resp;
    }

    @PostMapping("/zlm/on_record_mp4")
    @Operation(summary = "ZLM MP4 录像回调")
    public Map<String, Object> zlmOnRecordMp4(@RequestBody Map<String, Object> body) {
        if (body != null && !body.containsKey("file_path") && body.containsKey("file")) {
            body.put("file_path", body.get("file"));
        }
        return srsOnDvr(body);
    }

    @PostMapping("/health")
    public CommonResult<String> health() {
        return CommonResult.success("ok");
    }
}
