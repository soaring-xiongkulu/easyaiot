package com.basiclab.iot.video.inference.onnx;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;
import com.basiclab.iot.video.inference.ModelPathResolver;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Java port of Python {@code PlatePipeline} (detect + perspective + rec ONNX).
 */
@Slf4j
@Component
public class PlateOnnxEngine {

    private static final int DET_SIZE = 640;
    private static final float REC_MEAN = 0.588f;
    private static final float REC_STD = 0.193f;
    private static final String PLATE_CHARS =
            "#京沪津渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危"
                    + "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品";
    private static final String[] PLATE_COLORS = {"黑色", "白色", "黄色", "蓝色", "绿色"};

    private final ModelPathResolver modelPathResolver;
    private final OrtEnvironment env = OrtEnvironment.getEnvironment();
    private final Object lock = new Object();
    private final AtomicBoolean closed = new AtomicBoolean(false);

    private volatile OrtSession detectSession;
    private volatile OrtSession recSession;
    private volatile String detectInput;
    private volatile String recInput;

    public PlateOnnxEngine(ModelPathResolver modelPathResolver) {
        this.modelPathResolver = modelPathResolver;
    }

    public boolean isAvailable() {
        try {
            ensureLoaded();
            return detectSession != null && recSession != null;
        } catch (Exception ex) {
            return false;
        }
    }

    public List<Map<String, Object>> predict(BufferedImage bgr, float conf) throws OrtException {
        ensureLoaded();
        List<Detection> dets = detect(bgr, conf);
        List<Map<String, Object>> out = new ArrayList<>();
        for (Detection det : dets) {
            BufferedImage roi = fourPointTransform(bgr, det.landmarks);
            if (det.plateType == 1) {
                roi = splitMergeDoublePlate(roi);
            }
            RecResult rec = recognize(roi);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("plate_no", rec.plateNo);
            row.put("plate_color", rec.plateColor);
            row.put("detect_conf", det.conf);
            row.put("plate_type", det.plateType);
            row.put("rect", List.of(det.x1, det.y1, det.x2, det.y2));
            out.add(row);
        }
        return out;
    }

    public List<Map<String, Object>> predictBytes(byte[] imageBytes, float conf) throws Exception {
        return predict(ImageTensors.decode(imageBytes), conf);
    }

    public RecResult recognizeRoi(BufferedImage roiBgr) throws OrtException {
        ensureLoaded();
        return recognize(roiBgr);
    }

    private List<Detection> detect(BufferedImage bgr, float conf) throws OrtException {
        ImageTensors.LetterboxResult lb = ImageTensors.letterboxRgbNchw(bgr, DET_SIZE, 114);
        long[] shape = new long[]{1, 3, DET_SIZE, DET_SIZE};
        try (OnnxTensor input = OnnxTensor.createTensor(env, ImageTensors.wrap(lb.nchw()), shape)) {
            try (OrtSession.Result result = detectSession.run(Collections.singletonMap(detectInput, input))) {
                Object value = result.get(0).getValue();
                return decodeDetections(value, lb, bgr.getWidth(), bgr.getHeight(), conf);
            }
        }
    }

    private List<Detection> decodeDetections(
            Object value,
            ImageTensors.LetterboxResult lb,
            int imgW,
            int imgH,
            float confTh
    ) {
        float[][] rows = toRows(value);
        List<Detection> out = new ArrayList<>();
        for (float[] row : rows) {
            if (row.length < 14) {
                continue;
            }
            float score = row[4];
            if (score < confTh) {
                continue;
            }
            float[][] kpts = new float[4][2];
            for (int i = 0; i < 4; i++) {
                float x = (row[6 + i * 2] - lb.left()) / lb.ratio();
                float y = (row[7 + i * 2] - lb.top()) / lb.ratio();
                kpts[i][0] = x;
                kpts[i][1] = y;
            }
            int x1 = clamp((int) ((row[0] - lb.left()) / lb.ratio()), 0, imgW - 1);
            int y1 = clamp((int) ((row[1] - lb.top()) / lb.ratio()), 0, imgH - 1);
            int x2 = clamp((int) ((row[2] - lb.left()) / lb.ratio()), 0, imgW);
            int y2 = clamp((int) ((row[3] - lb.top()) / lb.ratio()), 0, imgH);
            out.add(new Detection(x1, y1, x2, y2, score, (int) row[5], kpts));
        }
        out.sort((a, b) -> Float.compare(b.conf, a.conf));
        return out;
    }

    private static float[][] toRows(Object value) {
        if (value instanceof float[][][] cube) {
            // [1,300,14]
            return cube[0];
        }
        if (value instanceof float[][] matrix) {
            return matrix;
        }
        throw new IllegalStateException("unexpected plate_detect output: " + value.getClass());
    }

    private RecResult recognize(BufferedImage roi) throws OrtException {
        float[] nchw = ImageTensors.plateRecNchw(roi, REC_MEAN, REC_STD);
        long[] shape = new long[]{1, 3, 48, 168};
        try (OnnxTensor input = OnnxTensor.createTensor(env, ImageTensors.wrap(nchw), shape)) {
            try (OrtSession.Result result = recSession.run(Collections.singletonMap(recInput, input))) {
                Object plateLogits = result.get(0).getValue();
                Object colorLogits = result.size() > 1 ? result.get(1).getValue() : null;
                String plateNo = decodePlate(argmaxPlate(plateLogits));
                String color = decodeColor(colorLogits);
                return new RecResult(plateNo, color);
            }
        }
    }

    private static int[] argmaxPlate(Object logits) {
        float[][] seq;
        if (logits instanceof float[][][] cube) {
            seq = cube[0];
        } else if (logits instanceof float[][] matrix) {
            seq = matrix;
        } else {
            throw new IllegalStateException("unexpected plate_logits: " + logits.getClass());
        }
        int[] idxs = new int[seq.length];
        for (int t = 0; t < seq.length; t++) {
            int best = 0;
            float bestV = Float.NEGATIVE_INFINITY;
            for (int c = 0; c < seq[t].length; c++) {
                if (seq[t][c] > bestV) {
                    bestV = seq[t][c];
                    best = c;
                }
            }
            idxs[t] = best;
        }
        return idxs;
    }

    private static String decodePlate(int[] indexes) {
        StringBuilder sb = new StringBuilder();
        int prev = 0;
        for (int value : indexes) {
            if (value != 0 && value != prev && value >= 0 && value < PLATE_CHARS.length()) {
                sb.append(PLATE_CHARS.charAt(value));
            }
            prev = value;
        }
        return sb.toString();
    }

    private static String decodeColor(Object colorLogits) {
        if (!(colorLogits instanceof float[][] matrix) || matrix.length == 0) {
            if (colorLogits instanceof float[][][] cube && cube.length > 0) {
                return decodeColor(cube[0]);
            }
            return "";
        }
        float[] row = matrix[0];
        int best = 0;
        float bestV = Float.NEGATIVE_INFINITY;
        for (int i = 0; i < row.length; i++) {
            if (row[i] > bestV) {
                bestV = row[i];
                best = i;
            }
        }
        return best >= 0 && best < PLATE_COLORS.length ? PLATE_COLORS[best] : "";
    }

    private static BufferedImage fourPointTransform(BufferedImage src, float[][] pts) {
        float[][] ordered = orderPoints(pts);
        float tlx = ordered[0][0], tly = ordered[0][1];
        float trx = ordered[1][0], try_ = ordered[1][1];
        float brx = ordered[2][0], bry = ordered[2][1];
        float blx = ordered[3][0], bly = ordered[3][1];
        int maxW = Math.max(
                (int) Math.hypot(brx - blx, bry - bly),
                (int) Math.hypot(trx - tlx, try_ - tly));
        int maxH = Math.max(
                (int) Math.hypot(trx - brx, try_ - bry),
                (int) Math.hypot(tlx - blx, tly - bly));
        maxW = Math.max(1, maxW);
        maxH = Math.max(1, maxH);
        // Approximate with bounding-box crop + scale (full perspective needs OpenCV).
        int minX = (int) Math.floor(Math.min(Math.min(tlx, trx), Math.min(brx, blx)));
        int minY = (int) Math.floor(Math.min(Math.min(tly, try_), Math.min(bry, bly)));
        int maxX = (int) Math.ceil(Math.max(Math.max(tlx, trx), Math.max(brx, blx)));
        int maxY = (int) Math.ceil(Math.max(Math.max(tly, try_), Math.max(bry, bly)));
        minX = clamp(minX, 0, src.getWidth() - 1);
        minY = clamp(minY, 0, src.getHeight() - 1);
        maxX = clamp(maxX, minX + 1, src.getWidth());
        maxY = clamp(maxY, minY + 1, src.getHeight());
        BufferedImage crop = src.getSubimage(minX, minY, maxX - minX, maxY - minY);
        return ImageTensors.resize(crop, maxW, maxH);
    }

    private static float[][] orderPoints(float[][] pts) {
        float[][] rect = new float[4][2];
        float[] sums = new float[4];
        float[] diffs = new float[4];
        for (int i = 0; i < 4; i++) {
            sums[i] = pts[i][0] + pts[i][1];
            diffs[i] = pts[i][1] - pts[i][0];
        }
        int tl = argMin(sums);
        int br = argMax(sums);
        int tr = argMin(diffs);
        int bl = argMax(diffs);
        rect[0] = pts[tl];
        rect[1] = pts[tr];
        rect[2] = pts[br];
        rect[3] = pts[bl];
        return rect;
    }

    /** Simplified double-plate merge: stack top/bottom halves. */
    private static BufferedImage splitMergeDoublePlate(BufferedImage roi) {
        int h = roi.getHeight();
        int w = roi.getWidth();
        if (h < 4) {
            return roi;
        }
        BufferedImage top = roi.getSubimage(0, 0, w, h / 2);
        BufferedImage bottom = roi.getSubimage(0, h / 2, w, h - h / 2);
        BufferedImage topR = ImageTensors.resize(top, Math.max(1, (int) (w * 0.7)), Math.max(1, h / 2));
        BufferedImage out = new BufferedImage(Math.max(topR.getWidth(), bottom.getWidth()),
                topR.getHeight() + bottom.getHeight(), BufferedImage.TYPE_3BYTE_BGR);
        Graphics2D g = out.createGraphics();
        g.drawImage(topR, 0, 0, null);
        g.drawImage(bottom, 0, topR.getHeight(), null);
        g.dispose();
        return out;
    }

    private static int argMin(float[] arr) {
        int idx = 0;
        float best = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] < best) {
                best = arr[i];
                idx = i;
            }
        }
        return idx;
    }

    private static int argMax(float[] arr) {
        int idx = 0;
        float best = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] > best) {
                best = arr[i];
                idx = i;
            }
        }
        return idx;
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    private void ensureLoaded() throws OrtException {
        if (detectSession != null && recSession != null) {
            return;
        }
        synchronized (lock) {
            if (detectSession != null && recSession != null) {
                return;
            }
            Path det = modelPathResolver.plateDetectModel();
            Path rec = modelPathResolver.plateRecModel();
            if (det == null || rec == null) {
                throw new OrtException("plate_detect.onnx / plate_rec.onnx not found");
            }
            OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
            detectSession = env.createSession(det.toString(), opts);
            recSession = env.createSession(rec.toString(), opts);
            detectInput = detectSession.getInputNames().iterator().next();
            recInput = recSession.getInputNames().iterator().next();
            log.info("PlateOnnxEngine loaded det={} rec={}", det, rec);
        }
    }

    @PreDestroy
    public void close() {
        if (!closed.compareAndSet(false, true)) {
            return;
        }
        synchronized (lock) {
            closeQuietly(detectSession);
            closeQuietly(recSession);
            detectSession = null;
            recSession = null;
        }
    }

    private static void closeQuietly(OrtSession session) {
        if (session == null) {
            return;
        }
        try {
            session.close();
        } catch (Exception ignored) {
        }
    }

    public record RecResult(String plateNo, String plateColor) {
    }

    private record Detection(int x1, int y1, int x2, int y2, float conf, int plateType, float[][] landmarks) {
    }
}
