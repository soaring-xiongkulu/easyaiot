package com.basiclab.iot.video.controller;

import com.basiclab.iot.video.domain.vo.VideoApiResponse;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.service.plate.PlateLibraryService;
import com.basiclab.iot.video.service.plate.PlateModelService;
import com.basiclab.iot.video.service.plate.PlateRecognitionService;
import com.basiclab.iot.video.support.RequestParams;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
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
@RequestMapping("/video/plate")
@RequiredArgsConstructor
public class PlateController {

    private final PlateModelService plateModelService;
    private final PlateLibraryService plateLibraryService;
    private final PlateRecognitionService plateRecognitionService;

    @GetMapping("/health")
    public VideoApiResponse<Map<String, Object>> health() {
        return VideoApiResponse.success(plateModelService.health());
    }

    @GetMapping("/model/status")
    public VideoApiResponse<Map<String, Object>> modelStatus() {
        return VideoApiResponse.success(plateModelService.modelStatus());
    }

    @PostMapping("/model/download")
    public VideoApiResponse<Map<String, Object>> modelDownload() {
        return VideoApiResponse.success("success", plateModelService.startDownload());
    }

    @GetMapping("/libraries")
    public VideoApiResponse<List<Map<String, Object>>> listLibraries(
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String is_enabled) {
        List<Map<String, Object>> data = plateLibraryService.listLibraries(search, RequestParams.matchedFilter(is_enabled));
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
        return VideoApiResponse.success(plateLibraryService.getLibrary(libraryId, includeEntries));
    }

    @PostMapping("/libraries")
    public VideoApiResponse<Map<String, Object>> createLibrary(@RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("success", plateLibraryService.createLibrary(body != null ? body : Map.of()));
    }

    @PutMapping("/libraries/{libraryId}")
    public VideoApiResponse<Map<String, Object>> updateLibrary(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("success", plateLibraryService.updateLibrary(libraryId, body != null ? body : Map.of()));
    }

    @DeleteMapping("/libraries/{libraryId}")
    public VideoApiResponse<Void> deleteLibrary(@PathVariable int libraryId) {
        plateLibraryService.deleteLibrary(libraryId);
        return VideoApiResponse.success("success", null);
    }

    @GetMapping("/libraries/{libraryId}/entries")
    public Map<String, Object> listEntries(
            @PathVariable int libraryId,
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int page_size) {
        Map<String, Object> data = plateLibraryService.listEntries(libraryId, search, page, page_size);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("code", 0);
        response.put("msg", "success");
        response.put("message", "success");
        response.putAll(data);
        return response;
    }

    @PostMapping(value = "/libraries/{libraryId}/entries", consumes = MediaType.APPLICATION_JSON_VALUE)
    public VideoApiResponse<Map<String, Object>> addEntryJson(
            @PathVariable int libraryId,
            @RequestBody Map<String, Object> body) throws Exception {
        boolean enabled = RequestParams.bool(body, "is_enabled", true);
        return VideoApiResponse.success("success", plateLibraryService.addEntry(
                libraryId,
                RequestParams.str(body, "plate_no"),
                RequestParams.strOrNull(body, "plate_color"),
                RequestParams.strOrNull(body, "owner_name"),
                RequestParams.strOrNull(body, "owner_phone"),
                RequestParams.strOrNull(body, "remark"),
                null,
                enabled));
    }

    @PostMapping(value = "/libraries/{libraryId}/entries", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public VideoApiResponse<Map<String, Object>> addEntryMultipart(
            @PathVariable int libraryId,
            @RequestParam(required = false) String plate_no,
            @RequestParam(required = false) String plate_color,
            @RequestParam(required = false) String owner_name,
            @RequestParam(required = false) String owner_phone,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) String is_enabled,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        boolean enabled = is_enabled == null
                || RequestParams.matchedFilter(is_enabled) == null
                || RequestParams.matchedFilter(is_enabled);
        byte[] bytes = file != null && !file.isEmpty() ? file.getBytes() : null;
        return VideoApiResponse.success("success", plateLibraryService.addEntry(
                libraryId,
                plate_no,
                plate_color,
                owner_name,
                owner_phone,
                remark,
                bytes,
                enabled));
    }

    @PutMapping(value = "/entries/{entryId}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public VideoApiResponse<Map<String, Object>> updateEntryJson(
            @PathVariable int entryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("success",
                plateLibraryService.updateEntry(entryId, body != null ? body : Map.of(), null));
    }

    @PutMapping(value = "/entries/{entryId}", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public VideoApiResponse<Map<String, Object>> updateEntryMultipart(
            @PathVariable int entryId,
            @RequestParam(required = false) String plate_no,
            @RequestParam(required = false) String plate_color,
            @RequestParam(required = false) String owner_name,
            @RequestParam(required = false) String owner_phone,
            @RequestParam(required = false) String remark,
            @RequestParam(required = false) String is_enabled,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        Map<String, Object> data = new LinkedHashMap<>();
        if (plate_no != null) {
            data.put("plate_no", plate_no);
        }
        if (plate_color != null) {
            data.put("plate_color", plate_color);
        }
        if (owner_name != null) {
            data.put("owner_name", owner_name);
        }
        if (owner_phone != null) {
            data.put("owner_phone", owner_phone);
        }
        if (remark != null) {
            data.put("remark", remark);
        }
        if (is_enabled != null) {
            data.put("is_enabled", is_enabled);
        }
        byte[] bytes = file != null && !file.isEmpty() ? file.getBytes() : null;
        return VideoApiResponse.success("success", plateLibraryService.updateEntry(entryId, data, bytes));
    }

    @DeleteMapping("/entries/{entryId}")
    public VideoApiResponse<Void> deleteEntry(@PathVariable int entryId) {
        plateLibraryService.deleteEntry(entryId);
        return VideoApiResponse.success("success", null);
    }

    @PostMapping("/entries/batch-delete")
    public VideoApiResponse<Map<String, Object>> batchDeleteEntries(@RequestBody(required = false) Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<Integer> entryIds = body != null
                ? (List<Integer>) (Object) RequestParams.list(body, "entry_ids", "entryIds") : List.of();
        return VideoApiResponse.success("success", plateLibraryService.batchDeleteEntries(entryIds));
    }

    @GetMapping("/libraries/{libraryId}/normalize/preview")
    public VideoApiResponse<List<Map<String, Object>>> previewNormalize(
            @PathVariable int libraryId,
            @RequestParam(required = false) String threshold) {
        double th = threshold != null && !threshold.isBlank() ? Double.parseDouble(threshold) : 1.0;
        List<Map<String, Object>> groups = plateLibraryService.previewNormalize(libraryId, th);
        VideoApiResponse<List<Map<String, Object>>> response = VideoApiResponse.success(groups);
        response.setTotal(groups.size());
        return response;
    }

    @PostMapping("/libraries/{libraryId}/normalize/merge")
    public VideoApiResponse<Map<String, Object>> mergeNormalize(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> payload = body != null ? body : Map.of();
        int targetEntryId = RequestParams.toInt(RequestParams.first(payload, "target_entry_id", "targetEntryId"), 0);
        if (targetEntryId <= 0) {
            throw new VideoBusinessException(400, "target_entry_id 不能为空");
        }
        @SuppressWarnings("unchecked")
        List<Integer> sourceIds = (List<Integer>) (Object) RequestParams.list(payload, "source_entry_ids", "sourceEntryIds");
        return VideoApiResponse.success("合并成功", plateLibraryService.mergeNormalize(libraryId, targetEntryId, sourceIds));
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
        double resolved = th != null && !String.valueOf(th).isBlank() ? Double.parseDouble(String.valueOf(th)) : 1.0;
        Map<String, Object> result = plateLibraryService.mergeAllNormalize(libraryId, resolved);
        String msg = "已合并 " + result.get("merged_groups") + " 组、" + result.get("merged_entries") + " 条重复车牌";
        return VideoApiResponse.success(msg, result);
    }

    @GetMapping("/libraries/{libraryId}/auto-enroll")
    public VideoApiResponse<Map<String, Object>> getAutoEnroll(@PathVariable int libraryId) {
        return VideoApiResponse.success(plateLibraryService.getAutoEnroll(libraryId));
    }

    @PutMapping("/libraries/{libraryId}/auto-enroll")
    public VideoApiResponse<Map<String, Object>> saveAutoEnroll(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body) {
        return VideoApiResponse.success("success", plateLibraryService.saveAutoEnroll(libraryId, body != null ? body : Map.of()));
    }

    @PostMapping("/libraries/{libraryId}/auto-enroll/start")
    public VideoApiResponse<Map<String, Object>> startAutoEnroll(@PathVariable int libraryId) {
        return VideoApiResponse.success("success", plateLibraryService.startAutoEnroll(libraryId));
    }

    @PostMapping("/libraries/{libraryId}/auto-enroll/stop")
    public VideoApiResponse<Map<String, Object>> stopAutoEnroll(@PathVariable int libraryId) {
        return VideoApiResponse.success("success", plateLibraryService.stopAutoEnroll(libraryId));
    }

    @PostMapping("/libraries/{libraryId}/match")
    public VideoApiResponse<Map<String, Object>> matchInLibrary(
            @PathVariable int libraryId,
            @RequestBody(required = false) Map<String, Object> body,
            @RequestParam(required = false) MultipartFile file) throws Exception {
        Map<String, Object> data = body != null ? body : Map.of();
        String plateNo = RequestParams.str(data, "plate_no", "plateNo");
        if (plateNo.isEmpty() && file != null && !file.isEmpty()) {
            List<Map<String, Object>> plates = plateRecognitionService.recognizePlates(file.getBytes());
            if (plates.isEmpty()) {
                Map<String, Object> empty = new LinkedHashMap<>();
                empty.put("matched", false);
                empty.put("plates", List.of());
                return VideoApiResponse.success("success", empty);
            }
            plateNo = String.valueOf(plates.get(0).get("plate_no"));
        }
        return VideoApiResponse.success("success", plateLibraryService.matchInLibrary(libraryId, plateNo));
    }

    @GetMapping("/matching/records")
    public VideoApiResponse<Map<String, Object>> listMatchRecords(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int page_size,
            @RequestParam(required = false) Integer library_id,
            @RequestParam(required = false) String device_id,
            @RequestParam(required = false) String matched,
            @RequestParam(required = false) String correlation_id,
            @RequestParam(required = false) String correlationId) {
        String corr = correlation_id != null ? correlation_id : correlationId;
        return VideoApiResponse.success(plateLibraryService.listMatchRecords(
                page, page_size, library_id, device_id, RequestParams.matchedFilter(matched), corr));
    }

    @PostMapping("/recognize/image")
    public VideoApiResponse<List<Map<String, Object>>> recognizeImage(
            @RequestParam(required = false) MultipartFile file) throws Exception {
        if (file == null || file.isEmpty()) {
            throw new com.basiclab.iot.video.exception.VideoBusinessException(400, "请上传车牌图片");
        }
        return VideoApiResponse.success("success", plateRecognitionService.recognizePlates(file.getBytes()));
    }

    @PostMapping("/recognize/device/{deviceId}/snapshot")
    public VideoApiResponse<List<Map<String, Object>>> recognizeDeviceSnapshot(@PathVariable String deviceId) {
        return VideoApiResponse.success("success", plateRecognitionService.recognizeDeviceSnapshot(deviceId));
    }
}
