package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.service.face.FaceLibraryService;
import com.basiclab.iot.video.service.face.FaceModelService;
import com.basiclab.iot.video.service.face.FaceRecognitionService;
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

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/video/face")
@RequiredArgsConstructor
public class FaceController {

    private final FaceModelService faceModelService;
    private final FaceLibraryService faceLibraryService;
    private final FaceRecognitionService faceRecognitionService;

    @GetMapping("/health")
    public VideoApiResponse<Map<String, Object>> health() {
        return VideoApiResponse.success(faceModelService.health());
    }

    @GetMapping("/model/status")
    public VideoApiResponse<Map<String, Object>> modelStatus() {
        return VideoApiResponse.success(faceModelService.modelStatus());
    }

    @PostMapping("/model/download")
    public VideoApiResponse<Map<String, Object>> modelDownload() {
        Map<String, Object> data = faceModelService.startDownload();
        return VideoApiResponse.success("success", data);
    }

    @GetMapping("/libraries")
    public VideoApiResponse<List<Map<String, Object>>> listLibraries(
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String is_enabled) {
        List<Map<String, Object>> data = faceLibraryService.listLibraries(search, RequestParams.matchedFilter(is_enabled));
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
        return VideoApiResponse.success(faceLibraryService.getLibrary(libraryId, includeEntries));
    }

    @PostMapping("/libraries")
    public VideoApiResponse<Map<String, Object>> createLibrary(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("创建成功", faceLibraryService.createLibrary(body != null ? body : Map.of()));
    }

    @PutMapping("/libraries/{libraryId}")
    public VideoApiResponse<Map<String, Object>> updateLibrary(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("更新成功", faceLibraryService.updateLibrary(libraryId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/libraries/{libraryId}")
    public VideoApiResponse<Void> deleteLibrary(@PathVariable int libraryId) {
        faceLibraryService.deleteLibrary(libraryId);
        return VideoApiResponse.success("删除成功", null);
    }

    @GetMapping("/libraries/{libraryId}/entries")
    public VideoApiResponse<List<Map<String, Object>>> listEntries(
            @PathVariable int libraryId,
            @RequestParam(required = false) String search) {
        List<Map<String, Object>> data = faceLibraryService.listEntries(libraryId, search);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(data);
        response.setTotal(data.size());
        return response;
    }

    @GetMapping("/libraries/{libraryId}/persons")
    public Map<String, Object> listPersons(
            @PathVariable int libraryId,
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "1") int pageNo,
            @RequestParam(defaultValue = "18") int pageSize,
            @RequestParam(required = false) Integer page_size) {
        int resolvedPage = pageNo > 0 ? pageNo : page;
        int resolvedSize = page_size != null ? page_size : pageSize;
        Map<String, Object> data = faceLibraryService.listPersons(libraryId, search, resolvedPage, resolvedSize);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("code", 0);
        response.put("msg", "success");
        response.put("message", "success");
        response.putAll(data);
        return response;
    }

    @GetMapping("/persons/{personId}")
    public VideoApiResponse<Map<String, Object>> getPerson(
            @PathVariable int personId,
            @RequestParam(defaultValue = "true") String include_entries) {
        boolean includeEntries = RequestParams.matchedFilter(include_entries) == null
                || RequestParams.matchedFilter(include_entries);
        return VideoApiResponse.success(faceLibraryService.getPerson(personId, includeEntries));
    }

    @DeleteMapping("/persons/{personId}")
    public VideoApiResponse<Void> deletePerson(@PathVariable int personId) {
        faceLibraryService.deletePerson(personId);
        return VideoApiResponse.success("删除成功", null);
    }

    @PostMapping("/persons/batch-delete")
    public VideoApiResponse<Map<String, Object>> batchDeletePersons(@RequestBody(required = false) Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<Integer> personIds = body != null
                ? (List<Integer>) (Object) RequestParams.list(body, "person_ids", "personIds") : List.of();
        return VideoApiResponse.success("删除成功", faceLibraryService.batchDeletePersons(personIds));
    }

    @PutMapping("/persons/{personId}/cover")
    public VideoApiResponse<Map<String, Object>> setPersonCover(
            @PathVariable int personId,
            @RequestBody(required = false) Map<String, Object> body) {
        int entryId = RequestParams.toInt(RequestParams.first(body != null ? body : Map.of(), "entry_id", "entryId"), 0);
        if (entryId <= 0) {
            throw new com.basiclab.iot.video.exception.VideoBusinessException(400, "entry_id 不能为空");
        }
        return VideoApiResponse.success("封面设置成功", faceLibraryService.setPersonCover(personId, entryId));
    }

    @PostMapping("/libraries/{libraryId}/entries")
    public VideoApiResponse<Map<String, Object>> addEntry(
            @PathVariable int libraryId,
            @RequestParam(required = false) String person_name,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String person_code,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) String is_enabled,
            @RequestParam(required = false) Integer person_id,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        String personName = person_name != null && !person_name.isBlank() ? person_name : name;
        byte[] bytes = file != null ? file.getBytes() : new byte[0];
        Integer personId = person_id;
        boolean enabled = is_enabled == null || RequestParams.matchedFilter(is_enabled) == null
                || RequestParams.matchedFilter(is_enabled);
        return VideoApiResponse.success("录入成功",
                faceLibraryService.addEntry(libraryId, personName, bytes, person_code, remark, personId, enabled));
    }

    @PostMapping("/libraries/{libraryId}/entries/batch")
    public VideoApiResponse<Map<String, Object>> addEntriesBatch(
            @PathVariable int libraryId,
            @RequestParam(required = false) String person_name,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String person_code,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) String is_enabled,
            @RequestParam(required = false) Integer person_id,
            @RequestParam(required = false) List<MultipartFile> files,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        String personName = person_name != null && !person_name.isBlank() ? person_name : name;
        List<byte[]> imageFiles = new java.util.ArrayList<>();
        if (files != null) {
            for (MultipartFile f : files) {
                if (f != null && !f.isEmpty()) {
                    imageFiles.add(f.getBytes());
                }
            }
        } else if (file != null && !file.isEmpty()) {
            imageFiles.add(file.getBytes());
        }
        boolean enabled = is_enabled == null || RequestParams.matchedFilter(is_enabled) == null
                || RequestParams.matchedFilter(is_enabled);
        Map<String, Object> result = faceLibraryService.addEntriesBatch(
                libraryId, personName, imageFiles, person_code, remark, person_id, enabled);
        int success = ((Number) result.get("success_count")).intValue();
        int failed = ((Number) result.getOrDefault("failed_count", 0)).intValue();
        String msg = "成功录入 " + success + " 张" + (failed > 0 ? "，" + failed + " 张失败" : "");
        return VideoApiResponse.success(msg, result);
    }

    @PutMapping("/entries/{entryId}")
    public VideoApiResponse<Map<String, Object>> updateEntry(
            @PathVariable int entryId,
            @RequestParam(required = false) String person_name,
            @RequestParam(required = false) String person_code,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) String is_enabled,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        Map<String, Object> data = new LinkedHashMap<>();
        if (person_name != null) {
            data.put("person_name", person_name);
        }
        if (person_code != null) {
            data.put("person_code", person_code);
        }
        if (remark != null) {
            data.put("remark", remark);
        }
        if (is_enabled != null) {
            data.put("is_enabled", RequestParams.matchedFilter(is_enabled));
        }
        byte[] bytes = file != null && !file.isEmpty() ? file.getBytes() : null;
        return VideoApiResponse.success("更新成功", faceLibraryService.updateEntry(entryId, bytes, data));
    }

    @DeleteMapping("/entries/{entryId}")
    public VideoApiResponse<Void> deleteEntry(@PathVariable int entryId) {
        faceLibraryService.deleteEntry(entryId);
        return VideoApiResponse.success("删除成功", null);
    }

    @GetMapping("/libraries/{libraryId}/auto-enroll")
    public VideoApiResponse<Map<String, Object>> getAutoEnroll(@PathVariable int libraryId) {
        return VideoApiResponse.success(faceLibraryService.getAutoEnroll(libraryId));
    }

    @PutMapping("/libraries/{libraryId}/auto-enroll")
    public VideoApiResponse<Map<String, Object>> saveAutoEnroll(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("保存成功", faceLibraryService.saveAutoEnroll(libraryId, body != null ? body : Map.of()));
    }

    @PostMapping("/libraries/{libraryId}/auto-enroll/start")
    public VideoApiResponse<Map<String, Object>> startAutoEnroll(@PathVariable int libraryId) {
        return VideoApiResponse.success("摄像头自动录入已开启", faceLibraryService.startAutoEnroll(libraryId));
    }

    @PostMapping("/libraries/{libraryId}/auto-enroll/stop")
    public VideoApiResponse<Map<String, Object>> stopAutoEnroll(@PathVariable int libraryId) {
        return VideoApiResponse.success("摄像头自动录入已关闭", faceLibraryService.stopAutoEnroll(libraryId));
    }

    @GetMapping("/libraries/{libraryId}/normalize/preview")
    public VideoApiResponse<List<Map<String, Object>>> previewNormalize(
            @PathVariable int libraryId,
            @RequestParam(required = false) String threshold) {
        double th = threshold != null && !threshold.isBlank() ? Double.parseDouble(threshold) : 0.75;
        List<Map<String, Object>> groups = faceLibraryService.previewNormalize(libraryId, th);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(groups);
        response.setTotal(groups.size());
        return response;
    }

    @PostMapping("/libraries/{libraryId}/normalize/merge")
    public VideoApiResponse<Map<String, Object>> mergeNormalize(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("合并成功", faceLibraryService.mergeNormalize(libraryId, body != null ? body : Map.of()));
    }

    @PostMapping("/libraries/{libraryId}/normalize/merge-all")
    public VideoApiResponse<Map<String, Object>> mergeAllNormalize(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body,
            @RequestParam(required = false) String threshold) {
        Object th = body != null ? RequestParams.first(body, "threshold") : null;
        if (th == null) {
            th = threshold;
        }
        double resolved = th != null && !String.valueOf(th).isBlank() ? Double.parseDouble(String.valueOf(th)) : 0.75;
        Map<String, Object> result = faceLibraryService.mergeAllNormalize(libraryId, resolved);
        return VideoApiResponse.success("已合并 " + result.get("merged_groups") + " 组、" + result.get("merged_persons") + " 人", result);
    }

    @PostMapping("/libraries/{libraryId}/match")
    public VideoApiResponse<Map<String, Object>> matchInLibrary(
            @PathVariable int libraryId,
            @RequestParam(required = false) String threshold,
            @RequestParam(defaultValue = "5") int top_k,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        Double th = threshold != null && !threshold.isBlank() ? Double.parseDouble(threshold) : null;
        byte[] bytes = file != null ? file.getBytes() : new byte[0];
        return VideoApiResponse.success("匹配完成", faceLibraryService.matchInLibrary(libraryId, bytes, th, top_k));
    }

    @GetMapping("/matching/records")
    public Map<String, Object> listMatchRecords(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) Integer page_size,
            @RequestParam(required = false) Integer library_id,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String matched,
            @RequestParam(required = false) String correlation_id,
            @RequestParam(required = false) String correlationId) {
        int resolvedSize = page_size != null ? page_size : pageSize;
        String corr = correlation_id != null ? correlation_id : correlationId;
        Map<String, Object> data = faceLibraryService.listMatchRecords(
                page, resolvedSize, library_id, device_id, RequestParams.matchedFilter(matched), corr);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("code", 0);
        response.put("msg", "success");
        response.put("message", "success");
        response.putAll(data);
        return response;
    }

    @GetMapping("/library")
    public VideoApiResponse<List<Map<String, Object>>> listLegacyLibrary(
            @RequestParam(required = false) String label,
            @RequestParam(defaultValue = "1000") int limit) {
        return VideoApiResponse.success(faceRecognitionService.listLegacyFaces(label, limit));
    }

    @PostMapping("/library")
    public VideoApiResponse<Map<String, Object>> addLegacyLibrary(
            @RequestParam String label,
            @RequestParam MultipartFile file) throws Exception {
        return VideoApiResponse.success("录入成功", faceRecognitionService.addLegacyFace(label, file.getBytes()));
    }

    @PutMapping("/library/{label}")
    public VideoApiResponse<Map<String, Object>> updateLegacyLibrary(
            @PathVariable String label,
            @RequestParam MultipartFile file) throws Exception {
        return VideoApiResponse.success("更新成功", faceRecognitionService.updateLegacyFace(label, file.getBytes()));
    }

    @DeleteMapping("/library/{label}")
    public VideoApiResponse<Map<String, Object>> deleteLegacyLibrary(@PathVariable String label) {
        return VideoApiResponse.success("删除成功", faceRecognitionService.deleteLegacyFace(label));
    }

    @PostMapping("/recognize/image")
    public VideoApiResponse<Map<String, Object>> recognizeImage(
            @RequestParam(defaultValue = "3") int top_k,
            @RequestParam(required = false) Integer library_id,
            @RequestParam(required = false) String threshold,
            @RequestParam MultipartFile file) throws Exception {
        Double th = threshold != null && !threshold.isBlank() ? Double.parseDouble(threshold) : null;
        return VideoApiResponse.success("识别完成",
                faceRecognitionService.recognize(file.getBytes(), top_k, library_id, th));
    }

    @PostMapping("/recognize/device/{deviceId}/snapshot")
    public VideoApiResponse<Map<String, Object>> recognizeDeviceSnapshot(
            @PathVariable String deviceId,
            @RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> payload = body != null ? body : Map.of();
        int topK = RequestParams.toInt(payload.get("top_k"), 3);
        Integer libraryId = payload.get("library_id") != null ? RequestParams.toInt(payload.get("library_id"), 0) : null;
        Double threshold = payload.get("threshold") != null ? RequestParams.toDouble(payload.get("threshold"), 0) : null;
        return VideoApiResponse.success("识别完成",
                faceRecognitionService.recognizeDeviceSnapshot(deviceId, topK, libraryId, threshold));
    }
}
