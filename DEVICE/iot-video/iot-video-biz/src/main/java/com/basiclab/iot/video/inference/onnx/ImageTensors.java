package com.basiclab.iot.video.inference.onnx;

import javax.imageio.ImageIO;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.FloatBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Shared image → CHW float tensor helpers for ORT (no OpenCV JNI).
 */
public final class ImageTensors {

    private ImageTensors() {
    }

    public static BufferedImage decode(byte[] bytes) throws IOException {
        BufferedImage img = ImageIO.read(new ByteArrayInputStream(bytes));
        if (img == null) {
            throw new IOException("unsupported image bytes");
        }
        return toBgr(img);
    }

    public static BufferedImage decodeFile(Path path) throws IOException {
        return decode(Files.readAllBytes(path));
    }

    public static BufferedImage toBgr(BufferedImage src) {
        if (src.getType() == BufferedImage.TYPE_3BYTE_BGR) {
            return src;
        }
        BufferedImage bgr = new BufferedImage(src.getWidth(), src.getHeight(), BufferedImage.TYPE_3BYTE_BGR);
        Graphics2D g = bgr.createGraphics();
        g.drawImage(src, 0, 0, null);
        g.dispose();
        return bgr;
    }

    public static BufferedImage resize(BufferedImage src, int width, int height) {
        BufferedImage out = new BufferedImage(width, height, BufferedImage.TYPE_3BYTE_BGR);
        Graphics2D g = out.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.drawImage(src, 0, 0, width, height, null);
        g.dispose();
        return out;
    }

    public static BufferedImage crop(BufferedImage src, int x1, int y1, int x2, int y2) {
        int w = Math.max(1, x2 - x1);
        int h = Math.max(1, y2 - y1);
        return src.getSubimage(x1, y1, w, h);
    }

    /**
     * InsightFace ArcFace blob: {@code (img - mean) / std}, NCHW RGB (swapRB=true).
     */
    public static float[] arcfaceNchw(BufferedImage bgr, int size, float mean, float std) {
        BufferedImage resized = resize(bgr, size, size);
        float[] out = new float[3 * size * size];
        int idxR = 0;
        int idxG = size * size;
        int idxB = 2 * size * size;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                int rgb = resized.getRGB(x, y);
                float r = ((rgb >> 16) & 0xff);
                float g = ((rgb >> 8) & 0xff);
                float b = (rgb & 0xff);
                // swapRB=true in cv2.dnn.blobFromImages → feed RGB
                out[idxR++] = (r - mean) / std;
                out[idxG++] = (g - mean) / std;
                out[idxB++] = (b - mean) / std;
            }
        }
        return out;
    }

    /** YOLO letterbox to square, RGB /255 NCHW. Returns tensor + meta. */
    public static LetterboxResult letterboxRgbNchw(BufferedImage bgr, int newSize, int padColor) {
        int h = bgr.getHeight();
        int w = bgr.getWidth();
        float ratio = Math.min((float) newSize / h, (float) newSize / w);
        int newW = Math.round(w * ratio);
        int newH = Math.round(h * ratio);
        float dw = (newSize - newW) / 2f;
        float dh = (newSize - newH) / 2f;
        BufferedImage resized = resize(bgr, newW, newH);
        BufferedImage padded = new BufferedImage(newSize, newSize, BufferedImage.TYPE_3BYTE_BGR);
        Graphics2D g = padded.createGraphics();
        g.setColor(new java.awt.Color(padColor, padColor, padColor));
        g.fillRect(0, 0, newSize, newSize);
        int left = Math.round(dw - 0.1f);
        int top = Math.round(dh - 0.1f);
        g.drawImage(resized, left, top, null);
        g.dispose();

        float[] out = new float[3 * newSize * newSize];
        int plane = newSize * newSize;
        for (int y = 0; y < newSize; y++) {
            for (int x = 0; x < newSize; x++) {
                int rgb = padded.getRGB(x, y);
                float r = ((rgb >> 16) & 0xff) / 255f;
                float gg = ((rgb >> 8) & 0xff) / 255f;
                float b = (rgb & 0xff) / 255f;
                int i = y * newSize + x;
                out[i] = r;
                out[plane + i] = gg;
                out[2 * plane + i] = b;
            }
        }
        return new LetterboxResult(out, ratio, left, top, newSize);
    }

    /** Plate rec: resize 168x48, (img/255 - mean)/std, NCHW BGR order as OpenCV. */
    public static float[] plateRecNchw(BufferedImage bgr, float mean, float std) {
        BufferedImage resized = resize(bgr, 168, 48);
        float[] out = new float[3 * 48 * 168];
        int plane = 48 * 168;
        for (int y = 0; y < 48; y++) {
            for (int x = 0; x < 168; x++) {
                int rgb = resized.getRGB(x, y);
                // OpenCV BGR channel order in preprocess_rec after resize
                float b = (rgb & 0xff) / 255f;
                float g = ((rgb >> 8) & 0xff) / 255f;
                float r = ((rgb >> 16) & 0xff) / 255f;
                int i = y * 168 + x;
                out[i] = (b - mean) / std;
                out[plane + i] = (g - mean) / std;
                out[2 * plane + i] = (r - mean) / std;
            }
        }
        return out;
    }

    public static FloatBuffer wrap(float[] data) {
        return FloatBuffer.wrap(data);
    }

    public static float[] l2Normalize(float[] feat) {
        double sum = 0;
        for (float v : feat) {
            sum += (double) v * v;
        }
        double norm = Math.sqrt(sum);
        float[] out = new float[feat.length];
        if (norm <= 0) {
            return out;
        }
        for (int i = 0; i < feat.length; i++) {
            out[i] = (float) (feat[i] / norm);
        }
        return out;
    }

    public static double cosine(float[] a, float[] b) {
        int n = Math.min(a.length, b.length);
        double dot = 0;
        double na = 0;
        double nb = 0;
        for (int i = 0; i < n; i++) {
            dot += a[i] * b[i];
            na += a[i] * a[i];
            nb += b[i] * b[i];
        }
        if (na <= 0 || nb <= 0) {
            return 0;
        }
        return dot / (Math.sqrt(na) * Math.sqrt(nb));
    }

    public static List<Double> toDoubleList(float[] feat) {
        List<Double> out = new ArrayList<>(feat.length);
        for (float v : feat) {
            out.add((double) v);
        }
        return out;
    }

    public static float[] fromDoubleList(List<Double> list) {
        float[] out = new float[list.size()];
        for (int i = 0; i < list.size(); i++) {
            out[i] = list.get(i).floatValue();
        }
        return out;
    }

    public record LetterboxResult(float[] nchw, float ratio, int left, int top, int size) {
    }

    public record BBox(int x1, int y1, int x2, int y2, float conf) {
    }
}
