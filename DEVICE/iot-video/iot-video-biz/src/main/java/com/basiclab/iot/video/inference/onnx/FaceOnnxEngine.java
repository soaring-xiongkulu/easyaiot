package com.basiclab.iot.video.inference.onnx;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;
import com.basiclab.iot.video.inference.ModelPathResolver;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.awt.image.BufferedImage;
import java.nio.file.Path;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * ArcFace ONNX embedder (Python InsightFace {@code get_feat} equivalent).
 */
@Slf4j
@Component
public class FaceOnnxEngine {

    private static final float MEAN = 127.5f;
    private static final float STD = 127.5f;
    private static final int SIZE = 112;

    private final ModelPathResolver modelPathResolver;
    private final OrtEnvironment env = OrtEnvironment.getEnvironment();
    private final Object lock = new Object();
    private final AtomicBoolean closed = new AtomicBoolean(false);

    private volatile OrtSession session;
    private volatile String inputName;
    private volatile Path loadedPath;

    public FaceOnnxEngine(ModelPathResolver modelPathResolver) {
        this.modelPathResolver = modelPathResolver;
    }

    public boolean isAvailable() {
        try {
            ensureLoaded();
            return session != null;
        } catch (Exception ex) {
            return false;
        }
    }

    public Path modelPath() {
        return modelPathResolver.faceRecModel();
    }

    public float[] embedCrop(BufferedImage cropBgr) throws OrtException {
        ensureLoaded();
        float[] nchw = ImageTensors.arcfaceNchw(cropBgr, SIZE, MEAN, STD);
        long[] shape = new long[]{1, 3, SIZE, SIZE};
        try (OnnxTensor input = OnnxTensor.createTensor(env, ImageTensors.wrap(nchw), shape)) {
            Map<String, OnnxTensor> feeds = Collections.singletonMap(inputName, input);
            try (OrtSession.Result result = session.run(feeds)) {
                Object value = result.get(0).getValue();
                float[] raw = flatten(value);
                return ImageTensors.l2Normalize(raw);
            }
        }
    }

    public float[] embedCropBytes(byte[] imageBytes) throws Exception {
        return embedCrop(ImageTensors.decode(imageBytes));
    }

    private void ensureLoaded() throws OrtException {
        if (session != null) {
            return;
        }
        synchronized (lock) {
            if (session != null) {
                return;
            }
            Path path = modelPathResolver.faceRecModel();
            if (path == null) {
                throw new OrtException("face_rec.onnx not found");
            }
            OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
            opts.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT);
            session = env.createSession(path.toString(), opts);
            inputName = session.getInputNames().iterator().next();
            loadedPath = path;
            log.info("FaceOnnxEngine loaded: {}", path);
        }
    }

    private static float[] flatten(Object value) {
        if (value instanceof float[][] matrix) {
            return matrix[0];
        }
        if (value instanceof float[] vector) {
            return vector;
        }
        if (value instanceof float[][][] cube) {
            return cube[0][0];
        }
        throw new IllegalStateException("unexpected ORT output type: " + value.getClass());
    }

    @PreDestroy
    public void close() {
        if (!closed.compareAndSet(false, true)) {
            return;
        }
        synchronized (lock) {
            if (session != null) {
                try {
                    session.close();
                } catch (Exception ignored) {
                }
                session = null;
            }
        }
    }

    public Path getLoadedPath() {
        return loadedPath;
    }
}
