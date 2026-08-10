package com.basiclab.iot.video.service.pose;

import com.basiclab.iot.video.support.JsonFields;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Pose intent similarity scoring, ported from Python {@code app.utils.pose_intent}.
 */
final class PoseIntentMatcher {

    private static final int NOSE = 0;
    private static final int L_SHOULDER = 5;
    private static final int R_SHOULDER = 6;
    private static final int L_ELBOW = 7;
    private static final int R_ELBOW = 8;
    private static final int L_WRIST = 9;
    private static final int R_WRIST = 10;
    private static final int L_HIP = 11;
    private static final int R_HIP = 12;
    private static final int L_KNEE = 13;
    private static final int R_KNEE = 14;
    private static final int L_ANKLE = 15;
    private static final int R_ANKLE = 16;

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private PoseIntentMatcher() {
    }

    static List<Map<String, Object>> matchTest(
            List<Map<String, Object>> persons,
            List<Map<String, Object>> entries,
            String matchMode,
            double threshold
    ) {
        List<Map<String, Object>> results = new ArrayList<>();
        String mode = matchMode != null && !matchMode.isBlank() ? matchMode : "angle";
        for (int pi = 0; pi < persons.size(); pi++) {
            List<double[]> keypoints = parseKeypoints(persons.get(pi).get("keypoints"));
            if (keypoints.isEmpty()) {
                continue;
            }
            Map<String, Object> best = null;
            double bestSim = -1.0;
            for (Map<String, Object> entry : entries) {
                double sim = matchPersonToEntry(keypoints, entry, mode);
                if (best == null || sim > bestSim) {
                    bestSim = sim;
                    best = new java.util.LinkedHashMap<>();
                    best.put("entry_id", entry.get("id"));
                    best.put("entry_name", entry.get("name"));
                    best.put("similarity", round4(sim));
                    best.put("matched", sim >= threshold);
                }
            }
            if (best != null) {
                best.put("person_index", pi);
                results.add(best);
            }
        }
        return results;
    }

    static List<Double> extractAngleFeatures(List<double[]> keypoints) {
        if (visibleKeypointCount(keypoints) < 4) {
            return null;
        }
        double scale = shoulderWidth(keypoints);
        double[] center = torsoCenter(keypoints);
        if (center == null) {
            center = new double[]{0.0, 0.0};
        }
        List<Double> features = new ArrayList<>();
        addAngle(features, keypoints, center, scale, L_SHOULDER, L_ELBOW, L_WRIST);
        addAngle(features, keypoints, center, scale, R_SHOULDER, R_ELBOW, R_WRIST);
        addAngle(features, keypoints, center, scale, L_HIP, L_KNEE, L_ANKLE);
        addAngle(features, keypoints, center, scale, R_HIP, R_KNEE, R_ANKLE);
        addAngle(features, keypoints, center, scale, L_SHOULDER, L_HIP, L_KNEE);
        addAngle(features, keypoints, center, scale, R_SHOULDER, R_HIP, R_KNEE);
        addAngle(features, keypoints, center, scale, L_SHOULDER, NOSE, R_SHOULDER);

        double[] ls = point(keypoints, center, scale, L_SHOULDER);
        double[] rs = point(keypoints, center, scale, R_SHOULDER);
        double[] lh = point(keypoints, center, scale, L_HIP);
        double[] rh = point(keypoints, center, scale, R_HIP);
        if (ls != null && rs != null && lh != null && rh != null) {
            double midShoulderX = (ls[0] + rs[0]) / 2.0;
            double midShoulderY = (ls[1] + rs[1]) / 2.0;
            double midHipX = (lh[0] + rh[0]) / 2.0;
            double midHipY = (lh[1] + rh[1]) / 2.0;
            double dx = midShoulderX - midHipX;
            double dy = midShoulderY - midHipY;
            double torsoAngle = Math.toDegrees(Math.atan2(Math.abs(dx), Math.abs(dy) + 1e-6));
            features.add(torsoAngle / 90.0);
        } else {
            features.add(-1.0);
        }

        double[] lw = point(keypoints, center, scale, L_WRIST);
        double[] rw = point(keypoints, center, scale, R_WRIST);
        if (lw != null && ls != null) {
            features.add((ls[1] - lw[1]) / 2.0);
        } else {
            features.add(-1.0);
        }
        if (rw != null && rs != null) {
            features.add((rs[1] - rw[1]) / 2.0);
        } else {
            features.add(-1.0);
        }

        double[] nose = point(keypoints, center, scale, NOSE);
        if (nose != null && lh != null && rh != null) {
            double midHipY = (lh[1] + rh[1]) / 2.0;
            features.add(nose[1] > midHipY ? 1.0 : 0.0);
        } else {
            features.add(-1.0);
        }
        return features;
    }

    private static double matchPersonToEntry(List<double[]> keypoints, Map<String, Object> entry, String matchMode) {
        String sourceType = entry.get("source_type") != null ? String.valueOf(entry.get("source_type")) : "image";
        Map<String, Object> extraRules = castRules(entry.get("extra_rules"));
        if ("rule".equals(sourceType) && extraRules != null && !extraRules.isEmpty()) {
            return evaluateExtraRules(keypoints, extraRules) ? 1.0 : 0.0;
        }
        List<Double> queryFeat = extractAngleFeatures(keypoints);
        if (queryFeat == null) {
            return 0.0;
        }
        double[] refFeat = parseFeatureVector(entry.get("feature_vector"));
        double sim = computePoseSimilarity(queryFeat, refFeat, matchMode);
        if (extraRules != null && !extraRules.isEmpty() && !evaluateExtraRules(keypoints, extraRules)) {
            sim *= 0.5;
        }
        return sim;
    }

    private static double computePoseSimilarity(List<Double> queryFeat, double[] refFeat, String mode) {
        if (refFeat == null || refFeat.length == 0 || queryFeat == null || queryFeat.isEmpty()) {
            return 0.0;
        }
        int len = Math.min(queryFeat.size(), refFeat.length);
        List<Double> qv = new ArrayList<>();
        List<Double> rv = new ArrayList<>();
        for (int i = 0; i < len; i++) {
            double q = queryFeat.get(i);
            double r = refFeat[i];
            if (q >= 0 && r >= 0) {
                qv.add(q);
                rv.add(r);
            }
        }
        if (qv.isEmpty()) {
            return 0.0;
        }
        if ("ratio".equals(mode)) {
            double sum = 0.0;
            for (int i = 0; i < qv.size(); i++) {
                sum += Math.abs(qv.get(i) - rv.get(i));
            }
            return Math.max(0.0, 1.0 - sum / qv.size());
        }
        double dot = 0.0;
        double normQ = 0.0;
        double normR = 0.0;
        for (int i = 0; i < qv.size(); i++) {
            dot += qv.get(i) * rv.get(i);
            normQ += qv.get(i) * qv.get(i);
            normR += rv.get(i) * rv.get(i);
        }
        if (normQ < 1e-9 || normR < 1e-9) {
            return 0.0;
        }
        double cosine = dot / (Math.sqrt(normQ) * Math.sqrt(normR));
        double angleSim = Math.max(0.0, Math.min(1.0, (cosine + 1.0) / 2.0));
        if ("combined".equals(mode)) {
            double sum = 0.0;
            for (int i = 0; i < qv.size(); i++) {
                sum += Math.abs(qv.get(i) - rv.get(i));
            }
            double ratioSim = Math.max(0.0, 1.0 - sum / qv.size());
            return 0.7 * angleSim + 0.3 * ratioSim;
        }
        return angleSim;
    }

    @SuppressWarnings("unchecked")
    private static boolean evaluateExtraRules(List<double[]> keypoints, Map<String, Object> rules) {
        int minKp = rules.get("min_visible_keypoints") instanceof Number n ? n.intValue() : 0;
        if (minKp > 0 && visibleKeypointCount(keypoints) < minKp) {
            return false;
        }
        double[] ls = raw(keypoints, L_SHOULDER);
        double[] rs = raw(keypoints, R_SHOULDER);
        double[] lh = raw(keypoints, L_HIP);
        double[] rh = raw(keypoints, R_HIP);
        double[] lw = raw(keypoints, L_WRIST);
        double[] rw = raw(keypoints, R_WRIST);
        double[] nose = raw(keypoints, NOSE);

        if (Boolean.TRUE.equals(rules.get("wrists_above_shoulder"))) {
            if (ls == null || rs == null || lw == null || rw == null) {
                return false;
            }
            if (!(lw[1] < ls[1] && rw[1] < rs[1])) {
                return false;
            }
        }
        if (Boolean.TRUE.equals(rules.get("head_below_hip")) && nose != null && lh != null && rh != null) {
            double midHipY = (lh[1] + rh[1]) / 2.0;
            if (nose[1] <= midHipY) {
                return false;
            }
        }
        Object maxTorso = rules.get("torso_ground_angle_max");
        if (maxTorso instanceof Number max && ls != null && rs != null && lh != null && rh != null) {
            double angle = torsoTilt(ls, rs, lh, rh);
            if (angle > max.doubleValue()) {
                return false;
            }
        }
        Object minTilt = rules.get("torso_tilt_min");
        if (minTilt instanceof Number min && ls != null && rs != null && lh != null && rh != null) {
            double angle = torsoTilt(ls, rs, lh, rh);
            if (angle < min.doubleValue()) {
                return false;
            }
        }
        Object kneeMax = rules.get("knee_angle_max");
        if (kneeMax instanceof Number knee && lh != null && rh != null) {
            double lk = kneeAngle(keypoints, lh, L_KNEE, L_ANKLE);
            double rk = kneeAngle(keypoints, rh, R_KNEE, R_ANKLE);
            if (Math.min(lk, rk) > knee.doubleValue()) {
                return false;
            }
        }
        return true;
    }

    private static double kneeAngle(List<double[]> keypoints, double[] hip, int kneeIdx, int ankleIdx) {
        double[] knee = raw(keypoints, kneeIdx);
        double[] ankle = raw(keypoints, ankleIdx);
        if (knee == null || ankle == null) {
            return 180.0;
        }
        return angleAt(new double[]{hip[0], hip[1]}, new double[]{knee[0], knee[1]}, new double[]{ankle[0], ankle[1]});
    }

    private static double torsoTilt(double[] ls, double[] rs, double[] lh, double[] rh) {
        double midShoulderX = (ls[0] + rs[0]) / 2.0;
        double midShoulderY = (ls[1] + rs[1]) / 2.0;
        double midHipX = (lh[0] + rh[0]) / 2.0;
        double midHipY = (lh[1] + rh[1]) / 2.0;
        double dx = midShoulderX - midHipX;
        double dy = midShoulderY - midHipY;
        return Math.toDegrees(Math.atan2(Math.abs(dx), Math.abs(dy) + 1e-6));
    }

    @SuppressWarnings("unchecked")
    private static List<double[]> parseKeypoints(Object raw) {
        List<double[]> out = new ArrayList<>();
        if (raw instanceof List<?> list) {
            for (Object item : list) {
                if (item instanceof List<?> kp && kp.size() >= 2) {
                    double x = toDouble(kp.get(0));
                    double y = toDouble(kp.get(1));
                    double c = kp.size() >= 3 ? toDouble(kp.get(2)) : 1.0;
                    out.add(new double[]{x, y, c});
                }
            }
        }
        return out;
    }

    private static double[] parseFeatureVector(Object raw) {
        if (raw == null) {
            return null;
        }
        if (raw instanceof List<?> list) {
            double[] arr = new double[list.size()];
            for (int i = 0; i < list.size(); i++) {
                arr[i] = toDouble(list.get(i));
            }
            return arr.length > 0 ? arr : null;
        }
        if (raw instanceof String text && !text.isBlank()) {
            List<Object> parsed = JsonFields.parseJsonList(text);
            if (!parsed.isEmpty()) {
                return parseFeatureVector(parsed);
            }
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castRules(Object raw) {
        if (raw instanceof Map<?, ?> map) {
            Map<String, Object> out = new java.util.LinkedHashMap<>();
            for (Map.Entry<?, ?> e : map.entrySet()) {
                out.put(String.valueOf(e.getKey()), e.getValue());
            }
            return out;
        }
        if (raw instanceof String text && !text.isBlank()) {
            try {
                return MAPPER.readValue(text, Map.class);
            } catch (Exception ignored) {
                return Map.of();
            }
        }
        return Map.of();
    }

    private static int visibleKeypointCount(List<double[]> keypoints) {
        int count = 0;
        for (double[] kp : keypoints) {
            if (kp.length >= 3 && kp[2] >= 0.25) {
                count++;
            }
        }
        return count;
    }

    private static double shoulderWidth(List<double[]> keypoints) {
        double[] ls = raw(keypoints, L_SHOULDER);
        double[] rs = raw(keypoints, R_SHOULDER);
        if (ls != null && rs != null) {
            return Math.max(hypot(ls[0] - rs[0], ls[1] - rs[1]), 1.0);
        }
        double[] lh = raw(keypoints, L_HIP);
        double[] rh = raw(keypoints, R_HIP);
        if (lh != null && rh != null) {
            return Math.max(hypot(lh[0] - rh[0], lh[1] - rh[1]), 1.0);
        }
        return 100.0;
    }

    private static double[] torsoCenter(List<double[]> keypoints) {
        List<double[]> pts = new ArrayList<>();
        for (int idx : new int[]{L_SHOULDER, R_SHOULDER, L_HIP, R_HIP}) {
            double[] p = raw(keypoints, idx);
            if (p != null) {
                pts.add(p);
            }
        }
        if (pts.size() < 2) {
            return null;
        }
        double x = 0.0;
        double y = 0.0;
        for (double[] p : pts) {
            x += p[0];
            y += p[1];
        }
        return new double[]{x / pts.size(), y / pts.size()};
    }

    private static double[] point(List<double[]> keypoints, double[] center, double scale, int idx) {
        double[] p = raw(keypoints, idx);
        if (p == null) {
            return null;
        }
        return new double[]{(p[0] - center[0]) / scale, (p[1] - center[1]) / scale};
    }

    private static double[] raw(List<double[]> keypoints, int idx) {
        if (idx >= keypoints.size()) {
            return null;
        }
        double[] kp = keypoints.get(idx);
        if (kp.length < 3 || kp[2] < 0.05) {
            return null;
        }
        return kp;
    }

    private static void addAngle(
            List<Double> features,
            List<double[]> keypoints,
            double[] center,
            double scale,
            int i,
            int j,
            int k
    ) {
        double[] a = point(keypoints, center, scale, i);
        double[] b = point(keypoints, center, scale, j);
        double[] c = point(keypoints, center, scale, k);
        if (a != null && b != null && c != null) {
            features.add(angleAt(a, b, c) / 180.0);
        } else {
            features.add(-1.0);
        }
    }

    private static double angleAt(double[] a, double[] b, double[] c) {
        double bax = a[0] - b[0];
        double bay = a[1] - b[1];
        double bcx = c[0] - b[0];
        double bcy = c[1] - b[1];
        double dot = bax * bcx + bay * bcy;
        double normBa = hypot(bax, bay);
        double normBc = hypot(bcx, bcy);
        if (normBa < 1e-6 || normBc < 1e-6) {
            return 0.0;
        }
        double cos = Math.max(-1.0, Math.min(1.0, dot / (normBa * normBc)));
        return Math.toDegrees(Math.acos(cos));
    }

    private static double hypot(double x, double y) {
        return Math.hypot(x, y);
    }

    private static double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        return Double.parseDouble(String.valueOf(value));
    }

    private static double round4(double value) {
        return Math.round(value * 10_000.0) / 10_000.0;
    }
}
