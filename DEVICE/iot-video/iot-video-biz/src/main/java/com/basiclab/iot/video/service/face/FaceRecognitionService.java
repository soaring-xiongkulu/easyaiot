package com.basiclab.iot.video.service.face;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.inference.PythonInferenceWorker;
import com.basiclab.iot.video.inference.PythonInferenceWorker.WorkerResult;
import com.basiclab.iot.video.inference.milvus.MilvusFaceVectorStore;
import com.basiclab.iot.video.inference.onnx.FaceDetOnnxEngine;
import com.basiclab.iot.video.inference.onnx.FaceOnnxEngine;
import com.basiclab.iot.video.inference.onnx.ImageTensors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Face recognition: Part2 Wave-A prefers ORT Java + milvus-sdk-java;
 * Python CLI only when {@code video.inference.python-cli-enabled=true}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class FaceRecognitionService {

    private static final String NO_ENGINE_MSG =
            "人脸推理引擎不可用（需 face_rec.onnx + Milvus；或开启 python-cli-enabled）";

    public static final String FACE_MODEL_MISSING_ENTRY_MSG =
            "人脸特征模型 face_rec.onnx 未安装，请在人脸库页面下载安装后再录入";

    private final VideoProperties videoProperties;
    private final PythonInferenceWorker pythonInferenceWorker;
    private final FaceOnnxEngine faceOnnxEngine;
    private final FaceDetOnnxEngine faceDetOnnxEngine;
    private final MilvusFaceVectorStore milvusFaceVectorStore;

    public boolean isEngineAvailable() {
        if (javaEngineReady()) {
            return true;
        }
        return pythonCliAllowed() && pythonInferenceWorker.isFaceEngineAvailable();
    }

    private boolean javaEngineReady() {
        VideoProperties.Inference inf = videoProperties.getInference();
        if (!inf.isOnnxEnabled()) {
            return false;
        }
        return faceOnnxEngine.isAvailable() && milvusFaceVectorStore.ping();
    }

    private boolean pythonCliAllowed() {
        VideoProperties.Inference inf = videoProperties.getInference();
        return inf.isEnabled() && inf.isPythonCliEnabled();
    }

    public void ensureFaceDetectable(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "上传文件不能为空");
        }
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(500, NO_ENGINE_MSG);
        }
    }

    public void validateFaceEntryImage(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传人脸照片");
        }
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(400, FACE_MODEL_MISSING_ENTRY_MSG);
        }
        if (!faceOnnxEngine.isAvailable() && !pythonCliAllowed()) {
            throw new VideoBusinessException(400, FACE_MODEL_MISSING_ENTRY_MSG);
        }
    }

    public FaceCropResult extractCropForEntry(byte[] imageBytes) {
        validateFaceEntryImage(imageBytes);
        if (javaEngineReady() || (faceOnnxEngine.isAvailable() && videoProperties.getInference().isOnnxEnabled())) {
            try {
                return extractCropJava(imageBytes);
            } catch (VideoBusinessException ex) {
                throw ex;
            } catch (Exception ex) {
                if (!pythonCliAllowed()) {
                    throw new VideoBusinessException(500, "人脸特征提取失败: " + ex.getMessage());
                }
                log.warn("Java face extract failed, fallback CLI: {}", ex.getMessage());
            }
        }
        if (!pythonCliAllowed()) {
            throw new VideoBusinessException(500, NO_ENGINE_MSG);
        }
        WorkerResult worker = pythonInferenceWorker.faceExtractCrop(imageBytes);
        if (!worker.ok()) {
            String err = worker.error() != null ? worker.error() : "人脸特征提取失败";
            if (err.contains("face_rec.onnx") || err.contains("未安装")) {
                throw new VideoBusinessException(400, FACE_MODEL_MISSING_ENTRY_MSG);
            }
            if (err.contains("未检测到人脸")) {
                throw new VideoBusinessException(400, err);
            }
            throw new VideoBusinessException(500, "人脸特征提取失败: " + err);
        }
        Object cropBase64 = worker.data().get("crop_jpeg_base64");
        if (cropBase64 == null || String.valueOf(cropBase64).isBlank()) {
            throw new VideoBusinessException(400, "图片中未检测到人脸，请上传正面清晰的人脸照片");
        }
        try {
            byte[] cropBytes = java.util.Base64.getDecoder().decode(String.valueOf(cropBase64));
            List<Double> embedding = castEmbeddingList(worker.data().get("embedding"));
            return new FaceCropResult(cropBytes, embedding);
        } catch (IllegalArgumentException ex) {
            throw new VideoBusinessException(500, "人脸特征提取失败: crop decode error");
        }
    }

    private FaceCropResult extractCropJava(byte[] imageBytes) throws Exception {
        BufferedImage image = ImageTensors.decode(imageBytes);
        BufferedImage crop = largestFaceCrop(image);
        float[] emb = faceOnnxEngine.embedCrop(crop);
        return new FaceCropResult(toJpeg(crop), ImageTensors.toDoubleList(emb));
    }

    private BufferedImage largestFaceCrop(BufferedImage image) throws Exception {
        if (faceDetOnnxEngine.isAvailable()) {
            List<ImageTensors.BBox> boxes = faceDetOnnxEngine.detect(image, 0.45f);
            if (!boxes.isEmpty()) {
                ImageTensors.BBox b = boxes.get(0);
                return ImageTensors.crop(image, b.x1(), b.y1(), b.x2(), b.y2());
            }
        }
        // Fallback: treat whole image as aligned crop (useful for enrollment face photos).
        if (image.getWidth() >= 32 && image.getHeight() >= 32) {
            log.info("face det empty — using full frame as crop {}x{}", image.getWidth(), image.getHeight());
            return image;
        }
        throw new VideoBusinessException(400, "图片中未检测到人脸，请上传正面清晰的人脸照片");
    }

    public String addFaceToLibrary(
            int libraryId,
            int faceEntryId,
            String personName,
            String personCode,
            List<Double> embedding
    ) {
        if (javaEngineReady() || milvusFaceVectorStore.ping()) {
            try {
                float[] vec = ImageTensors.fromDoubleList(embedding);
                return milvusFaceVectorStore.insertEmbedding(
                        vec, personName, libraryId, faceEntryId, personName, personCode);
            } catch (Exception ex) {
                if (!pythonCliAllowed()) {
                    throw new VideoBusinessException(500, "Milvus 入库失败: " + ex.getMessage());
                }
                log.warn("Java Milvus insert failed, fallback CLI: {}", ex.getMessage());
            }
        }
        if (!pythonCliAllowed()) {
            throw new VideoBusinessException(500, "Milvus 入库失败: engine unavailable");
        }
        WorkerResult worker = pythonInferenceWorker.faceAddToLibrary(
                libraryId, faceEntryId, personName, personCode, embedding);
        if (!worker.ok()) {
            throw new VideoBusinessException(500, "Milvus 入库失败: " + worker.error());
        }
        Object milvusId = worker.data().get("milvus_id");
        return milvusId != null ? String.valueOf(milvusId) : null;
    }

    public void deleteFaceByMilvusId(String milvusId) {
        if (milvusId == null || milvusId.isBlank()) {
            return;
        }
        try {
            if (milvusFaceVectorStore.ping()) {
                milvusFaceVectorStore.deleteByMilvusId(milvusId);
                return;
            }
        } catch (Exception ex) {
            log.warn("delete milvus_id {} via Java failed: {}", milvusId, ex.getMessage());
        }
        if (!pythonCliAllowed()) {
            return;
        }
        try {
            WorkerResult worker = pythonInferenceWorker.faceDeleteByMilvusId(milvusId);
            if (!worker.ok()) {
                log.warn("delete milvus_id {} failed: {}", milvusId, worker.error());
            }
        } catch (Exception ex) {
            log.warn("delete milvus_id {} failed: {}", milvusId, ex.getMessage());
        }
    }

    public record FaceCropResult(byte[] cropJpegBytes, List<Double> embedding) {}

    public Map<String, Object> recognize(byte[] imageBytes, int topK, Integer libraryId, Double threshold) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(500, "识别失败: " + NO_ENGINE_MSG);
        }
        if (javaEngineReady()) {
            try {
                return matchJava(imageBytes, libraryId, threshold != null ? threshold
                        : videoProperties.getInference().getFaceSimilarityThreshold(), topK);
            } catch (Exception ex) {
                if (!pythonCliAllowed()) {
                    throw new VideoBusinessException(500, "识别失败: " + ex.getMessage());
                }
                log.warn("Java recognize failed, fallback CLI: {}", ex.getMessage());
            }
        }
        if (!pythonCliAllowed()) {
            throw new VideoBusinessException(500, "识别失败: " + NO_ENGINE_MSG);
        }
        WorkerResult worker = pythonInferenceWorker.faceRecognize(imageBytes, libraryId, threshold, topK);
        if (!worker.ok()) {
            throw new VideoBusinessException(500, "识别失败: " + worker.error());
        }
        Object result = worker.data().get("result");
        if (result instanceof Map<?, ?> map) {
            return castMap(map);
        }
        throw new VideoBusinessException(500, "识别失败: worker 返回格式异常");
    }

    public Map<String, Object> recognizeDeviceSnapshot(String deviceId, int topK, Integer libraryId, Double threshold) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("device_id", deviceId);
        result.put("captured_at", java.time.Instant.now().toString());
        throw new VideoBusinessException(500, "识别失败: RTSP 抓帧失败");
    }

    public Map<String, Object> matchInLibrary(int libraryId, byte[] imageBytes, Double threshold, int topK) {
        ensureFaceDetectable(imageBytes);
        double useThreshold = threshold != null ? threshold
                : videoProperties.getInference().getFaceSimilarityThreshold();
        if (javaEngineReady()) {
            try {
                return matchJava(imageBytes, libraryId, useThreshold, topK);
            } catch (Exception ex) {
                if (!pythonCliAllowed()) {
                    Map<String, Object> empty = new LinkedHashMap<>();
                    empty.put("matched", false);
                    empty.put("candidates", List.of());
                    empty.put("threshold", useThreshold);
                    empty.put("error", ex.getMessage());
                    return empty;
                }
                log.warn("Java match failed, fallback CLI: {}", ex.getMessage());
            }
        }
        if (!pythonCliAllowed()) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("matched", false);
            empty.put("candidates", List.of());
            empty.put("threshold", useThreshold);
            return empty;
        }
        WorkerResult worker = pythonInferenceWorker.faceMatchInLibrary(
                writeTempImage(imageBytes), libraryId, useThreshold);
        if (!worker.ok()) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("matched", false);
            empty.put("candidates", List.of());
            empty.put("threshold", useThreshold);
            return empty;
        }
        Object nested = worker.data().get("result");
        if (nested instanceof Map<?, ?> map) {
            return castMap(map);
        }
        Map<String, Object> empty = new LinkedHashMap<>();
        empty.put("matched", false);
        empty.put("candidates", List.of());
        empty.put("threshold", useThreshold);
        return empty;
    }

    public Map<String, Object> matchImageFileInLibrary(int libraryId, String imagePath, double threshold) {
        if (imagePath == null || imagePath.isBlank()) {
            return emptyMatch(threshold);
        }
        if (!isEngineAvailable()) {
            Map<String, Object> empty = emptyMatch(threshold);
            empty.put("error", NO_ENGINE_MSG);
            return empty;
        }
        try {
            byte[] bytes = Files.readAllBytes(Path.of(imagePath));
            if (javaEngineReady()) {
                return matchJava(bytes, libraryId, threshold, 5);
            }
        } catch (Exception ex) {
            log.warn("Java match file failed libraryId={} path={}: {}", libraryId, imagePath, ex.getMessage());
            if (!pythonCliAllowed()) {
                return emptyMatch(threshold);
            }
        }
        if (!pythonCliAllowed()) {
            return emptyMatch(threshold);
        }
        WorkerResult worker = pythonInferenceWorker.faceMatchInLibrary(imagePath, libraryId, threshold);
        if (!worker.ok()) {
            log.warn("face match worker failed libraryId={} path={}: {}", libraryId, imagePath, worker.error());
            return emptyMatch(threshold);
        }
        Object nested = worker.data().get("result");
        if (nested instanceof Map<?, ?> map) {
            return castMap(map);
        }
        return emptyMatch(threshold);
    }

    private Map<String, Object> matchJava(byte[] imageBytes, Integer libraryId, double threshold, int topK)
            throws Exception {
        BufferedImage image = ImageTensors.decode(imageBytes);
        BufferedImage crop = largestFaceCrop(image);
        float[] emb = faceOnnxEngine.embedCrop(crop);
        List<Map<String, Object>> hits = milvusFaceVectorStore.searchEmbedding(emb, Math.max(1, topK), libraryId);
        List<Map<String, Object>> candidates = new ArrayList<>();
        boolean matched = false;
        Map<String, Object> best = null;
        for (Map<String, Object> hit : hits) {
            double sim = hit.get("similarity") instanceof Number n ? n.doubleValue() : 0d;
            Map<String, Object> c = new LinkedHashMap<>(hit);
            c.put("score", sim);
            candidates.add(c);
            if (sim >= threshold) {
                matched = true;
                if (best == null) {
                    best = c;
                }
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("matched", matched);
        out.put("threshold", threshold);
        out.put("candidates", candidates);
        out.put("engine", "onnx-milvus-java");
        if (best != null) {
            out.put("person_name", best.get("person_name"));
            out.put("person_code", best.get("person_code"));
            out.put("face_entry_id", best.get("face_entry_id"));
            out.put("similarity", best.get("similarity"));
            out.put("milvus_id", best.get("milvus_id"));
        }
        return out;
    }

    private static Map<String, Object> emptyMatch(double threshold) {
        Map<String, Object> empty = new LinkedHashMap<>();
        empty.put("matched", false);
        empty.put("candidates", List.of());
        empty.put("threshold", threshold);
        return empty;
    }

    public List<Map<String, Object>> listLegacyFaces(String label, int limit) {
        return List.of();
    }

    public Map<String, Object> addLegacyFace(String label, byte[] imageBytes) {
        if (label == null || label.isBlank()) {
            throw new VideoBusinessException(400, "label 不能为空");
        }
        ensureFaceDetectable(imageBytes);
        return Map.of("label", label);
    }

    public Map<String, Object> updateLegacyFace(String label, byte[] imageBytes) {
        if (label == null || label.isBlank()) {
            throw new VideoBusinessException(400, "label 不能为空");
        }
        ensureFaceDetectable(imageBytes);
        return Map.of("label", label);
    }

    public Map<String, Object> deleteLegacyFace(String label) {
        if (label == null || label.isBlank()) {
            throw new VideoBusinessException(400, "label 不能为空");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("label", label);
        result.put("deleted", 0);
        return result;
    }

    private static byte[] toJpeg(BufferedImage image) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(ImageTensors.toBgr(image), "jpg", baos);
        return baos.toByteArray();
    }

    private String writeTempImage(byte[] imageBytes) {
        try {
            Path tmp = Files.createTempFile("face-infer-", ".jpg");
            Files.write(tmp, imageBytes);
            return tmp.toString();
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "识别失败: 无法写入临时图片");
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castMap(Map<?, ?> map) {
        Map<String, Object> out = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            out.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        return out;
    }

    private static List<Double> castEmbeddingList(Object raw) {
        if (raw == null) {
            return List.of();
        }
        if (raw instanceof List<?> list) {
            List<Double> out = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof Number number) {
                    out.add(number.doubleValue());
                }
            }
            return out;
        }
        return List.of();
    }
}
