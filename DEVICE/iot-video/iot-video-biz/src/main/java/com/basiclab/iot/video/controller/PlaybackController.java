package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.PlaybackService;
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

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/playback")
@RequiredArgsConstructor
public class PlaybackController {

    private final PlaybackService playbackService;

    @GetMapping("/list")
    public VideoApiResponse<List<Map<String, Object>>> list(
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String start_time,
            @RequestParam(required = false) String end_time) {
        Map<String, Object> result = playbackService.list(pageNo, pageSize, search, device_id, start_time, end_time);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success((List<Map<String, Object>>) result.get("items"));
        response.setTotal(((Number) result.get("total")).intValue());
        return response;
    }

    @GetMapping("/{playbackId}")
    public VideoApiResponse<Map<String, Object>> get(@PathVariable int playbackId) {
        return VideoApiResponse.success(playbackService.get(playbackId));
    }

    @PostMapping({"", "/"})
    public VideoApiResponse<Map<String, Object>> create(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("录像回放记录创建成功", playbackService.create(body != null ? body : Map.of()));
    }

    @PutMapping("/{playbackId}")
    public VideoApiResponse<Map<String, Object>> update(
            @PathVariable int playbackId, @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("录像回放记录更新成功", playbackService.update(playbackId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/{playbackId}")
    public VideoApiResponse<Void> delete(@PathVariable int playbackId) {
        playbackService.delete(playbackId);
        return VideoApiResponse.success("录像回放记录删除成功", null);
    }

    @GetMapping("/thumbnail/{playbackId}")
    public VideoApiResponse<Map<String, Object>> thumbnail(@PathVariable int playbackId) {
        return VideoApiResponse.success(playbackService.thumbnail(playbackId));
    }

    @GetMapping("/statistics")
    public VideoApiResponse<Map<String, Object>> statistics(
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String start_time,
            @RequestParam(required = false) String end_time) {
        return VideoApiResponse.success(playbackService.statistics(device_id, start_time, end_time));
    }
}
