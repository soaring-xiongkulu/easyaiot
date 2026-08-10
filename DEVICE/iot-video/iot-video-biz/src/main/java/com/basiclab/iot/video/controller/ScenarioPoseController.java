package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.pose.ScenarioPoseLibraryService;
import com.basiclab.iot.video.support.RequestParams;
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
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/scenario-pose")
@RequiredArgsConstructor
public class ScenarioPoseController {

    private final ScenarioPoseLibraryService poseLibraryService;

    @GetMapping("/libraries")
    public VideoApiResponse<List<Map<String, Object>>> listLibraries(
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String is_enabled) {
        List<Map<String, Object>> data = poseLibraryService.listLibraries(search, RequestParams.matchedFilter(is_enabled));
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(data);
        response.setTotal(data.size());
        return response;
    }

    @GetMapping("/libraries/{libraryId}")
    public VideoApiResponse<Map<String, Object>> getLibrary(
            @PathVariable int libraryId,
            @RequestParam(defaultValue = "false") String include_entries) {
        boolean includeEntries = RequestParams.matchedFilter(include_entries) != null
                && RequestParams.matchedFilter(include_entries);
        return VideoApiResponse.success(poseLibraryService.getLibrary(libraryId, includeEntries));
    }

    @PostMapping("/libraries")
    public VideoApiResponse<Map<String, Object>> createLibrary(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("创建成功", poseLibraryService.createLibrary(body != null ? body : Map.of()));
    }

    @PutMapping("/libraries/{libraryId}")
    public VideoApiResponse<Map<String, Object>> updateLibrary(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("更新成功", poseLibraryService.updateLibrary(libraryId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/libraries/{libraryId}")
    public VideoApiResponse<Void> deleteLibrary(@PathVariable int libraryId) {
        poseLibraryService.deleteLibrary(libraryId);
        return VideoApiResponse.success("删除成功", null);
    }

    @GetMapping("/libraries/{libraryId}/entries")
    public VideoApiResponse<List<Map<String, Object>>> listEntries(
            @PathVariable int libraryId,
            @RequestParam(required = false) String search) {
        List<Map<String, Object>> data = poseLibraryService.listEntries(libraryId, search);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(data);
        response.setTotal(data.size());
        return response;
    }

    @PostMapping("/libraries/{libraryId}/entries")
    public VideoApiResponse<Map<String, Object>> addEntry(
            @PathVariable int libraryId,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) String conf,
            @RequestParam(required = false) MultipartFile file,
            @RequestBody(required = false) Map<String, Object> body) throws Exception {
        Map<String, Object> data = body != null ? body : Map.of();
        String entryName = name != null ? name : RequestParams.str(data, "name");
        if (entryName.isBlank()) {
            entryName = "参考姿态";
        }
        String entryRemark = remark != null ? remark : RequestParams.strOrNull(data, "remark");
        double confidence = conf != null
                ? RequestParams.toDouble(conf, 0.25)
                : RequestParams.toDouble(data.get("conf"), 0.25);
        byte[] bytes = file != null && !file.isEmpty() ? file.getBytes() : null;
        return VideoApiResponse.success("添加成功",
                poseLibraryService.addEntry(libraryId, entryName, entryRemark, confidence, bytes, data));
    }

    @PutMapping("/entries/{entryId}")
    public VideoApiResponse<Map<String, Object>> updateEntry(
            @PathVariable int entryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("更新成功",
                poseLibraryService.updateEntry(entryId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/entries/{entryId}")
    public VideoApiResponse<Void> deleteEntry(@PathVariable int entryId) {
        poseLibraryService.deleteEntry(entryId);
        return VideoApiResponse.success("删除成功", null);
    }

    @PostMapping("/entries/{entryId}/re-extract")
    public VideoApiResponse<Map<String, Object>> reExtractEntry(
            @PathVariable int entryId,
            @RequestBody(required = false) Map<String, Object> body) {
        double conf = body != null ? RequestParams.toDouble(body.get("conf"), 0.25) : 0.25;
        return VideoApiResponse.success("重新提取成功", poseLibraryService.reExtractEntry(entryId, conf));
    }

    @PostMapping("/entries/extract")
    public VideoApiResponse<Map<String, Object>> extractPreview(
            @RequestParam(required = false) String conf,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        double confidence = conf != null ? RequestParams.toDouble(conf, 0.25) : 0.25;
        byte[] bytes = file != null && !file.isEmpty() ? file.getBytes() : null;
        if (bytes == null || bytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        return VideoApiResponse.success(poseLibraryService.extractPreview(bytes, confidence));
    }

    @PostMapping("/libraries/{libraryId}/match-test")
    public VideoApiResponse<List<Map<String, Object>>> matchTest(
            @PathVariable int libraryId,
            @RequestParam(required = false) String conf,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        double confidence = conf != null ? RequestParams.toDouble(conf, 0.25) : 0.25;
        byte[] bytes = file != null && !file.isEmpty() ? file.getBytes() : null;
        if (bytes == null || bytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        return VideoApiResponse.success(poseLibraryService.matchTest(libraryId, bytes, confidence));
    }

    @GetMapping("/scene-templates")
    public VideoApiResponse<List<Map<String, Object>>> listSceneTemplates() {
        return VideoApiResponse.success(poseLibraryService.listSceneTemplates());
    }

    @PostMapping("/libraries/{libraryId}/import-template")
    public VideoApiResponse<Map<String, Object>> importTemplate(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> data = body != null ? body : Map.of();
        String templateKey = RequestParams.str(data, "template_key", "key");
        if (templateKey.isEmpty()) {
            throw new VideoBusinessException(400, "template_key 不能为空");
        }
        return VideoApiResponse.success("导入成功", poseLibraryService.importSceneTemplate(libraryId, templateKey));
    }
}
