package com.basiclab.iot.video.tools;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;
import com.basiclab.iot.video.inference.onnx.ImageTensors;
import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.MutationResult;
import io.milvus.grpc.SearchResults;
import io.milvus.param.ConnectParam;
import io.milvus.param.MetricType;
import io.milvus.param.R;
import io.milvus.param.collection.FlushParam;
import io.milvus.param.collection.HasCollectionParam;
import io.milvus.param.collection.LoadCollectionParam;
import io.milvus.param.dml.DeleteParam;
import io.milvus.param.dml.InsertParam;
import io.milvus.param.dml.SearchParam;
import io.milvus.response.SearchResultsWrapper;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.BufferedWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Standalone Part2 Wave-A evidence runner (no Spring).
 * Usage: java -cp iot-video-biz.jar com.basiclab.iot.video.tools.Part2WaveAEvidenceMain &lt;cmd&gt; ...
 */
public final class Part2WaveAEvidenceMain {

    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.err.println("cmds: embed <img> <out.json> | milvus-ping <out.json> | match-cycle <img> <out.json> | plate <img> <out.json>");
            System.exit(2);
        }
        String cmd = args[0];
        switch (cmd) {
            case "embed" -> embed(Path.of(args[1]), Path.of(args[2]));
            case "milvus-ping" -> milvusPing(Path.of(args[1]));
            case "match-cycle" -> matchCycle(Path.of(args[1]), Path.of(args[2]));
            case "plate" -> plate(Path.of(args[1]), Path.of(args[2]));
            default -> throw new IllegalArgumentException("unknown cmd " + cmd);
        }
    }

    private static void embed(Path image, Path out) throws Exception {
        Path model = Path.of("F:/acme/.worktrees/video-java/VIDEO/face_rec.onnx");
        long t0 = System.currentTimeMillis();
        float[] emb = embedImage(model, image);
        long ms = System.currentTimeMillis() - t0;
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("task", "A1");
        json.put("engine", "onnxruntime-java");
        json.put("model", model.toString().replace('\\', '/'));
        json.put("image", image.toString().replace('\\', '/'));
        json.put("dim", emb.length);
        json.put("elapsed_ms", ms);
        json.put("embedding", toList(emb));
        json.put("l2_norm", l2(emb));
        writeJson(out, json);
        System.out.println("WROTE " + out + " dim=" + emb.length + " ms=" + ms);
    }

    private static void milvusPing(Path out) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("task", "A2");
        try {
            MilvusServiceClient client = client();
            R<Boolean> has = client.hasCollection(HasCollectionParam.newBuilder()
                    .withCollectionName("face_embeddings").build());
            json.put("status", has.getStatus() == R.Status.Success.getCode() ? "PASS" : "FAIL");
            json.put("milvus_uri", "http://127.0.0.1:19530");
            json.put("collection_name", "face_embeddings");
            json.put("collection_exists", has.getData());
            // lightweight search with zero vector to prove RPC
            client.loadCollection(LoadCollectionParam.newBuilder()
                    .withCollectionName("face_embeddings").build());
            float[] zeros = new float[512];
            R<SearchResults> search = client.search(SearchParam.newBuilder()
                    .withCollectionName("face_embeddings")
                    .withMetricType(MetricType.IP)
                    .withTopK(1)
                    .withVectors(List.of(toFloatList(zeros)))
                    .withVectorFieldName("embedding")
                    .withParams("{\"nprobe\":16}")
                    .withOutFields(List.of("label"))
                    .build());
            json.put("search_ok", search.getStatus() == R.Status.Success.getCode());
            json.put("search_message", search.getMessage());
            client.close();
        } catch (Exception ex) {
            json.put("status", "BLOCKED");
            json.put("error", ex.getMessage());
        }
        writeJson(out, json);
        System.out.println("WROTE " + out + " " + json.get("status"));
    }

    private static void matchCycle(Path image, Path out) throws Exception {
        Path model = Path.of("F:/acme/.worktrees/video-java/VIDEO/face_rec.onnx");
        float[] emb = embedImage(model, image);
        MilvusServiceClient client = client();
        client.loadCollection(LoadCollectionParam.newBuilder()
                .withCollectionName("face_embeddings").build());
        long libraryId = 900012L;
        long entryId = System.currentTimeMillis() % 1_000_000_000L;
        List<InsertParam.Field> fields = List.of(
                new InsertParam.Field("library_id", List.of(libraryId)),
                new InsertParam.Field("face_entry_id", List.of(entryId)),
                new InsertParam.Field("label", List.of("p2a-wave-a")),
                new InsertParam.Field("person_name", List.of("p2a-person")),
                new InsertParam.Field("person_code", List.of("P2A001")),
                new InsertParam.Field("embedding", List.of(toFloatList(emb)))
        );
        R<MutationResult> inserted = client.insert(InsertParam.newBuilder()
                .withCollectionName("face_embeddings").withFields(fields).build());
        client.flush(FlushParam.newBuilder().withCollectionNames(List.of("face_embeddings")).build());
        long milvusId = inserted.getData().getIDs().getIntId().getDataList().get(0);

        R<SearchResults> hitSearch = client.search(SearchParam.newBuilder()
                .withCollectionName("face_embeddings")
                .withMetricType(MetricType.IP)
                .withTopK(3)
                .withVectors(List.of(toFloatList(emb)))
                .withVectorFieldName("embedding")
                .withExpr("library_id == " + libraryId)
                .withParams("{\"nprobe\":16}")
                .withOutFields(List.of("person_name", "face_entry_id", "label"))
                .build());
        SearchResultsWrapper hitWrap = new SearchResultsWrapper(hitSearch.getData().getResults());
        List<SearchResultsWrapper.IDScore> hitScores = hitWrap.getIDScore(0);
        boolean matched = !hitScores.isEmpty() && hitScores.get(0).getScore() >= 0.55f;

        // miss: random orthogonal-ish vector
        float[] missVec = new float[512];
        for (int i = 0; i < 512; i++) {
            missVec[i] = (i % 2 == 0) ? 0.02f : -0.02f;
        }
        missVec = ImageTensors.l2Normalize(missVec);
        R<SearchResults> missSearch = client.search(SearchParam.newBuilder()
                .withCollectionName("face_embeddings")
                .withMetricType(MetricType.IP)
                .withTopK(3)
                .withVectors(List.of(toFloatList(missVec)))
                .withVectorFieldName("embedding")
                .withExpr("library_id == " + libraryId)
                .withParams("{\"nprobe\":16}")
                .withOutFields(List.of("person_name"))
                .build());
        SearchResultsWrapper missWrap = new SearchResultsWrapper(missSearch.getData().getResults());
        List<SearchResultsWrapper.IDScore> missScores = missWrap.getIDScore(0);
        boolean missOk = missScores.isEmpty() || missScores.get(0).getScore() < 0.55f;

        client.delete(DeleteParam.newBuilder()
                .withCollectionName("face_embeddings")
                .withExpr("id == " + milvusId)
                .build());
        client.flush(FlushParam.newBuilder().withCollectionNames(List.of("face_embeddings")).build());
        client.close();

        Map<String, Object> json = new LinkedHashMap<>();
        json.put("task", "A3");
        json.put("status", matched && missOk ? "PASS" : "FAIL");
        json.put("engine", "onnx-milvus-java");
        json.put("bypassed", false);
        json.put("library_id", libraryId);
        json.put("milvus_id", milvusId);
        json.put("hit", Map.of(
                "matched", matched,
                "top_score", hitScores.isEmpty() ? 0 : hitScores.get(0).getScore(),
                "person_name", hitScores.isEmpty() ? null : hitScores.get(0).get("person_name")
        ));
        json.put("miss", Map.of(
                "matched", !missOk,
                "top_score", missScores.isEmpty() ? 0 : missScores.get(0).getScore()
        ));
        writeJson(out, json);
        System.out.println("WROTE " + out + " " + json.get("status"));
    }

    private static void plate(Path image, Path out) throws Exception {
        Path det = Path.of("F:/acme/.worktrees/video-java/VIDEO/plate_detect.onnx");
        Path rec = Path.of("F:/acme/.worktrees/video-java/VIDEO/plate_rec.onnx");
        // Use PlateOnnxEngine via reflection-free minimal path: detect+rec through same classes on classpath
        com.basiclab.iot.video.inference.onnx.PlateOnnxEngine engine =
                new com.basiclab.iot.video.inference.onnx.PlateOnnxEngine(null);
        // PlateOnnxEngine needs ModelPathResolver — instead inline ORT like Face embed for det/rec is huge.
        // Fall back: call Python plate pipeline for expected, and Java ImageIO + note engine class present.
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("task", "A4");
        json.put("note", "use scripts/p2a_plate_java_runner via Spring; standalone skipped resolver");
        json.put("det_model_exists", Files.isRegularFile(det));
        json.put("rec_model_exists", Files.isRegularFile(rec));
        json.put("image", image.toString().replace('\\', '/'));
        writeJson(out, json);
        System.out.println("WROTE stub " + out);
    }

    private static float[] embedImage(Path model, Path image) throws Exception {
        OrtEnvironment env = OrtEnvironment.getEnvironment();
        try (OrtSession session = env.createSession(model.toString(), new OrtSession.SessionOptions())) {
            BufferedImage bgr = ImageTensors.toBgr(ImageIO.read(image.toFile()));
            float[] nchw = ImageTensors.arcfaceNchw(bgr, 112, 127.5f, 127.5f);
            String inputName = session.getInputNames().iterator().next();
            try (OnnxTensor input = OnnxTensor.createTensor(env, ImageTensors.wrap(nchw), new long[]{1, 3, 112, 112})) {
                try (OrtSession.Result result = session.run(Collections.singletonMap(inputName, input))) {
                    Object value = result.get(0).getValue();
                    float[] raw;
                    if (value instanceof float[][] m) {
                        raw = m[0];
                    } else if (value instanceof float[] v) {
                        raw = v;
                    } else {
                        throw new IllegalStateException("bad output " + value.getClass());
                    }
                    return ImageTensors.l2Normalize(raw);
                }
            }
        }
    }

    private static MilvusServiceClient client() {
        return new MilvusServiceClient(ConnectParam.newBuilder()
                .withHost("127.0.0.1").withPort(19530).build());
    }

    private static List<Float> toFloatList(float[] arr) {
        List<Float> list = new ArrayList<>(arr.length);
        for (float v : arr) {
            list.add(v);
        }
        return list;
    }

    private static List<Double> toList(float[] arr) {
        List<Double> list = new ArrayList<>(arr.length);
        for (float v : arr) {
            list.add((double) v);
        }
        return list;
    }

    private static double l2(float[] arr) {
        double s = 0;
        for (float v : arr) {
            s += v * v;
        }
        return Math.sqrt(s);
    }

    private static void writeJson(Path out, Map<String, Object> json) {
        try {
            Files.createDirectories(out.getParent());
            String body = toJson(json);
            try (BufferedWriter w = Files.newBufferedWriter(out)) {
                w.write(body);
            }
            Path tracked = Path.of("F:/acme/.worktrees/video-java/.superpowers/sdd/evidence").resolve(out.getFileName());
            Files.createDirectories(tracked.getParent());
            Files.writeString(tracked, body);
        } catch (Exception ex) {
            throw new RuntimeException(ex);
        }
    }

    private static String toJson(Object obj) {
        // minimal JSON without Jackson dependency issues in shaded jar — use simple recursive builder
        if (obj == null) {
            return "null";
        }
        if (obj instanceof String s) {
            return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
        }
        if (obj instanceof Number || obj instanceof Boolean) {
            return String.valueOf(obj);
        }
        if (obj instanceof Map<?, ?> map) {
            StringBuilder sb = new StringBuilder();
            sb.append("{");
            boolean first = true;
            for (Map.Entry<?, ?> e : map.entrySet()) {
                if (!first) {
                    sb.append(",");
                }
                first = false;
                sb.append(toJson(String.valueOf(e.getKey()))).append(":").append(toJson(e.getValue()));
            }
            sb.append("}");
            return sb.toString();
        }
        if (obj instanceof List<?> list) {
            StringBuilder sb = new StringBuilder();
            sb.append("[");
            for (int i = 0; i < list.size(); i++) {
                if (i > 0) {
                    sb.append(",");
                }
                sb.append(toJson(list.get(i)));
            }
            sb.append("]");
            return sb.toString();
        }
        return toJson(String.valueOf(obj));
    }
}
