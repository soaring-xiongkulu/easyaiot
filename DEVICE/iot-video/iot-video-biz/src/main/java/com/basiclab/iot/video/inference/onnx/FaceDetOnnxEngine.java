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
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * YOLO-style face/head detector for {@code face_det.onnx} output shape {@code [1,5,N]}.
 */
@Slf4j
@Component
public class FaceDetOnnxEngine {

    private static final int INPUT = 640;
    private static final float DEFAULT_CONF = 0.45f;

    private final ModelPathResolver modelPathResolver;
    private final OrtEnvironment env = OrtEnvironment.getEnvironment();
    private final Object lock = new Object();
    private final AtomicBoolean closed = new AtomicBoolean(false);

    private volatile OrtSession session;
    private volatile String inputName;

    public FaceDetOnnxEngine(ModelPathResolver modelPathResolver) {
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

    public List<ImageTensors.BBox> detect(BufferedImage bgr, Float confThreshold) throws OrtException {
        ensureLoaded();
        float confTh = confThreshold != null ? confThreshold : DEFAULT_CONF;
        ImageTensors.LetterboxResult lb = ImageTensors.letterboxRgbNchw(bgr, INPUT, 114);
        long[] shape = new long[]{1, 3, INPUT, INPUT};
        try (OnnxTensor input = OnnxTensor.createTensor(env, ImageTensors.wrap(lb.nchw()), shape)) {
            Map<String, OnnxTensor> feeds = Collections.singletonMap(inputName, input);
            try (OrtSession.Result result = session.run(feeds)) {
                Object value = result.get(0).getValue();
                return decode(value, lb, bgr.getWidth(), bgr.getHeight(), confTh);
            }
        }
    }

    private List<ImageTensors.BBox> decode(
            Object value,
            ImageTensors.LetterboxResult lb,
            int imgW,
            int imgH,
            float confTh
    ) {
        float[][] data = toCN(value);
        // data[c][i] with c in {cx,cy,w,h,conf}
        int n = data[0].length;
        List<ImageTensors.BBox> boxes = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            float conf = data.length > 4 ? data[4][i] : 0f;
            if (conf < confTh) {
                continue;
            }
            float cx = data[0][i];
            float cy = data[1][i];
            float bw = data[2][i];
            float bh = data[3][i];
            float x1 = (cx - bw / 2f - lb.left()) / lb.ratio();
            float y1 = (cy - bh / 2f - lb.top()) / lb.ratio();
            float x2 = (cx + bw / 2f - lb.left()) / lb.ratio();
            float y2 = (cy + bh / 2f - lb.top()) / lb.ratio();
            int ix1 = clamp((int) Math.floor(x1), 0, imgW - 1);
            int iy1 = clamp((int) Math.floor(y1), 0, imgH - 1);
            int ix2 = clamp((int) Math.ceil(x2), 0, imgW);
            int iy2 = clamp((int) Math.ceil(y2), 0, imgH);
            if (ix2 <= ix1 || iy2 <= iy1) {
                continue;
            }
            boxes.add(new ImageTensors.BBox(ix1, iy1, ix2, iy2, conf));
        }
        boxes.sort(Comparator.comparingDouble(ImageTensors.BBox::conf).reversed());
        return nms(boxes, 0.5f);
    }

    private static List<ImageTensors.BBox> nms(List<ImageTensors.BBox> boxes, float iouTh) {
        List<ImageTensors.BBox> kept = new ArrayList<>();
        boolean[] removed = new boolean[boxes.size()];
        for (int i = 0; i < boxes.size(); i++) {
            if (removed[i]) {
                continue;
            }
            ImageTensors.BBox a = boxes.get(i);
            kept.add(a);
            for (int j = i + 1; j < boxes.size(); j++) {
                if (removed[j]) {
                    continue;
                }
                if (iou(a, boxes.get(j)) >= iouTh) {
                    removed[j] = true;
                }
            }
        }
        return kept;
    }

    private static float iou(ImageTensors.BBox a, ImageTensors.BBox b) {
        int x1 = Math.max(a.x1(), b.x1());
        int y1 = Math.max(a.y1(), b.y1());
        int x2 = Math.min(a.x2(), b.x2());
        int y2 = Math.min(a.y2(), b.y2());
        int inter = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
        int areaA = Math.max(0, a.x2() - a.x1()) * Math.max(0, a.y2() - a.y1());
        int areaB = Math.max(0, b.x2() - b.x1()) * Math.max(0, b.y2() - b.y1());
        int uni = areaA + areaB - inter;
        return uni <= 0 ? 0f : (float) inter / uni;
    }

    private static float[][] toCN(Object value) {
        if (value instanceof float[][][] cube) {
            // [1,5,N]
            return cube[0];
        }
        if (value instanceof float[][] matrix) {
            // [5,N] or [N,5]
            if (matrix.length == 5) {
                return matrix;
            }
            if (matrix.length > 0 && matrix[0].length == 5) {
                float[][] cn = new float[5][matrix.length];
                for (int i = 0; i < matrix.length; i++) {
                    for (int c = 0; c < 5; c++) {
                        cn[c][i] = matrix[i][c];
                    }
                }
                return cn;
            }
        }
        throw new IllegalStateException("unexpected face_det output: " + value.getClass());
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    private void ensureLoaded() throws OrtException {
        if (session != null) {
            return;
        }
        synchronized (lock) {
            if (session != null) {
                return;
            }
            Path path = modelPathResolver.faceDetModel();
            if (path == null) {
                throw new OrtException("face_det.onnx not found");
            }
            OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
            session = env.createSession(path.toString(), opts);
            inputName = session.getInputNames().iterator().next();
            log.info("FaceDetOnnxEngine loaded: {}", path);
        }
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
}
