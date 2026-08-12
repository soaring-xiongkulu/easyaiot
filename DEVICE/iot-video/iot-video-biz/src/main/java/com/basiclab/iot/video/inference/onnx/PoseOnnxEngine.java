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
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * YOLO Pose (COCO-17) via ORT Java — replaces {@code pose_inference_cli.py}.
 * Expects Ultralytics export: output shape roughly {@code [1, 56, N]} (4 box + 1 score + 51 kpt).
 */
@Slf4j
@Component
public class PoseOnnxEngine {

    private static final int INPUT_SIZE = 640;
    private static final int NUM_KPT = 17;
    private static final int KPT_DIM = 3; // x,y,conf

    private final ModelPathResolver modelPathResolver;
    private final OrtEnvironment env = OrtEnvironment.getEnvironment();
    private final Object lock = new Object();
    private final AtomicBoolean closed = new AtomicBoolean(false);

    private volatile OrtSession session;
    private volatile String inputName;
    private volatile Path loadedPath;

    public PoseOnnxEngine(ModelPathResolver modelPathResolver) {
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
        return modelPathResolver.poseModel();
    }

    public List<Map<String, Object>> extractPersons(BufferedImage bgr, double conf) throws OrtException {
        ensureLoaded();
        ImageTensors.LetterboxResult lb = ImageTensors.letterboxRgbNchw(bgr, INPUT_SIZE, 114);
        long[] shape = new long[]{1, 3, INPUT_SIZE, INPUT_SIZE};
        try (OnnxTensor input = OnnxTensor.createTensor(env, ImageTensors.wrap(lb.nchw()), shape);
             OrtSession.Result result = session.run(Collections.singletonMap(inputName, input))) {
            Object value = result.get(0).getValue();
            return decode(value, lb, bgr.getWidth(), bgr.getHeight(), (float) conf);
        }
    }

    public List<Map<String, Object>> extractPersonsBytes(byte[] imageBytes, double conf) throws Exception {
        return extractPersons(ImageTensors.decode(imageBytes), conf);
    }

    private List<Map<String, Object>> decode(
            Object value,
            ImageTensors.LetterboxResult lb,
            int origW,
            int origH,
            float confThresh
    ) {
        float[][] preds = toPredictions(value);
        if (preds.length == 0) {
            return List.of();
        }
        List<Candidate> candidates = new ArrayList<>();
        int dim0 = preds.length;
        int dim1 = preds[0].length;

        // Ultralytics end2end export: [N, 56|57] = xyxy + score + [cls] + 17*3 kpts
        // Raw export: [C, A] e.g. [56, 8400]
        boolean end2end = dim1 >= 56 && dim1 <= 64 && dim0 <= 1000;
        if (end2end) {
            for (float[] row : preds) {
                float score = row[4];
                if (score < confThresh) {
                    continue;
                }
                candidates.add(fromEnd2End(row, score, lb, origW, origH));
            }
        } else {
            boolean transposed = dim0 < dim1 && dim0 >= 6;
            if (!transposed) {
                for (float[] row : preds) {
                    if (row.length < 5 + NUM_KPT) {
                        continue;
                    }
                    float score = row[4];
                    if (score < confThresh) {
                        continue;
                    }
                    candidates.add(fromXywh(row, score, lb, origW, origH));
                }
            } else {
                for (int a = 0; a < dim1; a++) {
                    float score = preds[4][a];
                    if (score < confThresh) {
                        continue;
                    }
                    float[] row = new float[dim0];
                    for (int c = 0; c < dim0; c++) {
                        row[c] = preds[c][a];
                    }
                    candidates.add(fromXywh(row, score, lb, origW, origH));
                }
            }
        }

        List<Candidate> kept = nms(candidates, 0.45f);
        List<Map<String, Object>> out = new ArrayList<>(kept.size());
        for (Candidate c : kept) {
            Map<String, Object> person = new LinkedHashMap<>();
            person.put("keypoints", c.keypoints);
            person.put("keypointCount", c.keypoints.size());
            person.put("poseType", "body17");
            person.put("feature_vector", null);
            person.put("score", c.score);
            person.put("bbox", List.of(c.x1, c.y1, c.x2, c.y2));
            out.add(person);
        }
        return out;
    }

    /** End2end rows: x1,y1,x2,y2,score,[cls],kpts... in letterbox pixels. */
    private static Candidate fromEnd2End(
            float[] row,
            float score,
            ImageTensors.LetterboxResult lb,
            int origW,
            int origH
    ) {
        float x1 = (row[0] - lb.left()) / lb.ratio();
        float y1 = (row[1] - lb.top()) / lb.ratio();
        float x2 = (row[2] - lb.left()) / lb.ratio();
        float y2 = (row[3] - lb.top()) / lb.ratio();
        int base = row.length >= 6 + NUM_KPT * KPT_DIM ? 6 : 5;
        return buildCandidate(x1, y1, x2, y2, score, row, base, lb, origW, origH);
    }

    private static Candidate fromXywh(
            float[] row,
            float score,
            ImageTensors.LetterboxResult lb,
            int origW,
            int origH
    ) {
        float cx = row[0];
        float cy = row[1];
        float w = row[2];
        float h = row[3];
        float x1 = (cx - w / 2f - lb.left()) / lb.ratio();
        float y1 = (cy - h / 2f - lb.top()) / lb.ratio();
        float x2 = (cx + w / 2f - lb.left()) / lb.ratio();
        float y2 = (cy + h / 2f - lb.top()) / lb.ratio();
        int base = 5;
        if (row.length < 5 + NUM_KPT * KPT_DIM) {
            base = 4;
        }
        return buildCandidate(x1, y1, x2, y2, score, row, base, lb, origW, origH);
    }

    private static Candidate buildCandidate(
            float x1,
            float y1,
            float x2,
            float y2,
            float score,
            float[] row,
            int kptBase,
            ImageTensors.LetterboxResult lb,
            int origW,
            int origH
    ) {
        List<List<Double>> kps = new ArrayList<>(NUM_KPT);
        for (int k = 0; k < NUM_KPT; k++) {
            int i = kptBase + k * KPT_DIM;
            if (i + 2 >= row.length) {
                kps.add(List.of(0.0, 0.0, 0.0));
                continue;
            }
            double kx = (row[i] - lb.left()) / lb.ratio();
            double ky = (row[i + 1] - lb.top()) / lb.ratio();
            double kc = row[i + 2];
            kps.add(List.of(
                    round1(clamp(kx, 0, origW)),
                    round1(clamp(ky, 0, origH)),
                    round4(Math.max(0, Math.min(1, kc)))
            ));
        }
        Candidate c = new Candidate();
        c.x1 = (int) Math.max(0, Math.min(origW - 1, Math.round(x1)));
        c.y1 = (int) Math.max(0, Math.min(origH - 1, Math.round(y1)));
        c.x2 = (int) Math.max(0, Math.min(origW - 1, Math.round(x2)));
        c.y2 = (int) Math.max(0, Math.min(origH - 1, Math.round(y2)));
        c.score = score;
        c.keypoints = kps;
        return c;
    }

    private static float[][] toPredictions(Object value) {
        if (value instanceof float[][][] arr3) {
            // [1, C, N] or [1, N, C]
            float[][] plane = arr3[0];
            return plane;
        }
        if (value instanceof float[][] arr2) {
            return arr2;
        }
        if (value instanceof float[] flat) {
            // unlikely single dim
            return new float[][]{flat};
        }
        throw new IllegalArgumentException("unexpected pose output type: " + value.getClass());
    }

    private static List<Candidate> nms(List<Candidate> boxes, float iouThresh) {
        boxes.sort((a, b) -> Float.compare(b.score, a.score));
        List<Candidate> kept = new ArrayList<>();
        boolean[] removed = new boolean[boxes.size()];
        for (int i = 0; i < boxes.size(); i++) {
            if (removed[i]) {
                continue;
            }
            Candidate a = boxes.get(i);
            kept.add(a);
            for (int j = i + 1; j < boxes.size(); j++) {
                if (removed[j]) {
                    continue;
                }
                if (iou(a, boxes.get(j)) > iouThresh) {
                    removed[j] = true;
                }
            }
        }
        return kept;
    }

    private static float iou(Candidate a, Candidate b) {
        int xx1 = Math.max(a.x1, b.x1);
        int yy1 = Math.max(a.y1, b.y1);
        int xx2 = Math.min(a.x2, b.x2);
        int yy2 = Math.min(a.y2, b.y2);
        int w = Math.max(0, xx2 - xx1);
        int h = Math.max(0, yy2 - yy1);
        float inter = w * h;
        float union = (a.x2 - a.x1) * (a.y2 - a.y1) + (float) (b.x2 - b.x1) * (b.y2 - b.y1) - inter;
        return union <= 0 ? 0 : inter / union;
    }

    private static double clamp(double v, double lo, double hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    private static double round1(double v) {
        return Math.round(v * 10.0) / 10.0;
    }

    private static double round4(double v) {
        return Math.round(v * 10000.0) / 10000.0;
    }

    private void ensureLoaded() throws OrtException {
        if (session != null) {
            return;
        }
        synchronized (lock) {
            if (session != null) {
                return;
            }
            Path model = modelPathResolver.poseModel();
            if (model == null) {
                throw new OrtException("pose ONNX missing (yolo26n-pose.onnx)");
            }
            OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
            session = env.createSession(model.toString(), opts);
            inputName = session.getInputNames().iterator().next();
            loadedPath = model;
            log.info("PoseOnnxEngine loaded {}", model);
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
                    // ignore
                }
                session = null;
            }
        }
    }

    private static final class Candidate {
        int x1;
        int y1;
        int x2;
        int y2;
        float score;
        List<List<Double>> keypoints;
    }
}
