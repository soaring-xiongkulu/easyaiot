package com.basiclab.iot.video.service.face;

import com.basiclab.iot.video.inference.PythonInferenceWorker;
import com.basiclab.iot.video.inference.PythonInferenceWorker.WorkerResult;
import com.basiclab.iot.video.support.VideoModelPaths;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Face model + Milvus health — mirrors Python {@code face.py} health + {@code get_face_rec_model_status}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class FaceModelService {

    private final VideoModelPaths videoModelPaths;
    private final PythonInferenceWorker pythonInferenceWorker;

    /**
     * Python {@code face.py} L83-90: {@code get_face_vector_store().ping()} +
     * {@code recognition_model_loaded}/{@code recognition_model_downloading}.
     */
    public Map<String, Object> health() {
        Map<String, Object> data = new LinkedHashMap<>();
        WorkerResult ping = pythonInferenceWorker.faceVectorStorePing();
        if (ping.ok()) {
            putIfPresent(data, ping.data(), "milvus_uri");
            putIfPresent(data, ping.data(), "collection_name");
            putIfPresent(data, ping.data(), "collection_exists");
            if (ping.data().get("error") != null) {
                data.put("error", String.valueOf(ping.data().get("error")));
            }
        } else {
            data.put("milvus_uri", videoModelPaths.milvusUri());
            data.put("collection_name", videoModelPaths.faceMilvusCollection());
            data.put("collection_exists", false);
            data.put("error", ping.error() != null ? ping.error() : "Milvus ping failed");
        }
        boolean modelReady = videoModelPaths.isFaceRecModelReady();
        data.put("recognition_model_loaded", modelReady);
        data.put("recognition_model_downloading", false);
        return data;
    }

    /** Python {@code get_face_rec_model_status()} keys. */
    public Map<String, Object> modelStatus() {
        Path modelPath = videoModelPaths.faceRecModelPath();
        boolean exists = videoModelPaths.isFaceRecModelReady();
        long sizeBytes = videoModelPaths.faceRecModelSizeBytes();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("exists", exists);
        data.put("filename", modelPath.getFileName().toString());
        data.put("path", modelPath.toString().replace('\\', '/'));
        data.put("size_bytes", sizeBytes);
        data.put("downloading", false);
        data.put("resumable", false);
        data.put("stage", exists ? "done" : "idle");
        data.put("progress", exists ? 100 : 0);
        data.put("downloaded_bytes", exists ? sizeBytes : 0);
        data.put("total_bytes", exists ? sizeBytes : 0);
        data.put("error", null);
        return data;
    }

    public Map<String, Object> startDownload() {
        Map<String, Object> data = modelStatus();
        data.put("started", false);
        return data;
    }

    private static void putIfPresent(Map<String, Object> target, Map<String, Object> source, String key) {
        if (source.containsKey(key)) {
            target.put(key, source.get(key));
        }
    }
}
