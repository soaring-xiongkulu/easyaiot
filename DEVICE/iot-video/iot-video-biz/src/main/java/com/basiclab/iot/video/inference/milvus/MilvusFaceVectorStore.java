package com.basiclab.iot.video.inference.milvus;

import com.basiclab.iot.video.config.VideoProperties;
import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.DataType;
import io.milvus.grpc.MutationResult;
import io.milvus.grpc.SearchResults;
import io.milvus.param.ConnectParam;
import io.milvus.param.IndexType;
import io.milvus.param.MetricType;
import io.milvus.param.R;
import io.milvus.param.RpcStatus;
import io.milvus.param.collection.CreateCollectionParam;
import io.milvus.param.collection.FieldType;
import io.milvus.param.collection.HasCollectionParam;
import io.milvus.param.collection.LoadCollectionParam;
import io.milvus.param.dml.DeleteParam;
import io.milvus.param.dml.InsertParam;
import io.milvus.param.dml.SearchParam;
import io.milvus.param.index.CreateIndexParam;
import io.milvus.response.SearchResultsWrapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * milvus-sdk-java face vector store (schema aligned with Python {@code FaceVectorStore}).
 */
@Slf4j
@Component
public class MilvusFaceVectorStore {

    private static final int DIM = 512;

    private final VideoProperties videoProperties;
    private final Object lock = new Object();
    private final AtomicBoolean closed = new AtomicBoolean(false);

    private volatile MilvusServiceClient client;
    private volatile boolean collectionReady;

    public MilvusFaceVectorStore(VideoProperties videoProperties) {
        this.videoProperties = videoProperties;
    }

    public String milvusUri() {
        String env = System.getenv("MILVUS_URI");
        if (env != null && !env.isBlank()) {
            return env.trim();
        }
        return videoProperties.getInference().getMilvusUri();
    }

    public String collectionName() {
        String env = System.getenv("FACE_MILVUS_COLLECTION");
        if (env != null && !env.isBlank()) {
            return env.trim();
        }
        return videoProperties.getInference().getFaceMilvusCollection();
    }

    public boolean ping() {
        try {
            ensureClient();
            R<Boolean> has = client.hasCollection(HasCollectionParam.newBuilder()
                    .withCollectionName(collectionName())
                    .build());
            return has.getStatus() == R.Status.Success.getCode();
        } catch (Exception ex) {
            log.debug("Milvus ping failed: {}", ex.getMessage());
            return false;
        }
    }

    public Map<String, Object> pingDetail() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("milvus_uri", milvusUri());
        out.put("collection_name", collectionName());
        try {
            ensureClient();
            ensureCollection();
            out.put("collection_exists", true);
            out.put("ok", true);
        } catch (Exception ex) {
            out.put("collection_exists", false);
            out.put("ok", false);
            out.put("error", ex.getMessage());
        }
        return out;
    }

    public String insertEmbedding(
            float[] embedding,
            String label,
            int libraryId,
            int faceEntryId,
            String personName,
            String personCode
    ) {
        ensureCollection();
        List<InsertParam.Field> fields = new ArrayList<>();
        fields.add(new InsertParam.Field("library_id", List.of((long) libraryId)));
        fields.add(new InsertParam.Field("face_entry_id", List.of((long) faceEntryId)));
        fields.add(new InsertParam.Field("label", List.of(nullToEmpty(label))));
        fields.add(new InsertParam.Field("person_name", List.of(nullToEmpty(personName))));
        fields.add(new InsertParam.Field("person_code", List.of(nullToEmpty(personCode))));
        fields.add(new InsertParam.Field("embedding", List.of(toList(embedding))));

        R<MutationResult> result = client.insert(InsertParam.newBuilder()
                .withCollectionName(collectionName())
                .withFields(fields)
                .build());
        if (result.getStatus() != R.Status.Success.getCode()) {
            throw new IllegalStateException("Milvus insert failed: " + result.getMessage());
        }
        client.flush(io.milvus.param.collection.FlushParam.newBuilder()
                .withCollectionNames(List.of(collectionName()))
                .build());
        List<Long> ids = result.getData().getIDs().getIntId().getDataList();
        return ids.isEmpty() ? null : String.valueOf(ids.get(0));
    }

    public void deleteByMilvusId(String milvusId) {
        if (milvusId == null || milvusId.isBlank()) {
            return;
        }
        ensureCollection();
        R<MutationResult> result = client.delete(DeleteParam.newBuilder()
                .withCollectionName(collectionName())
                .withExpr("id == " + Long.parseLong(milvusId.trim()))
                .build());
        if (result.getStatus() != R.Status.Success.getCode()) {
            throw new IllegalStateException("Milvus delete failed: " + result.getMessage());
        }
        client.flush(io.milvus.param.collection.FlushParam.newBuilder()
                .withCollectionNames(List.of(collectionName()))
                .build());
    }

    public List<Map<String, Object>> searchEmbedding(float[] embedding, int topK, Integer libraryId) {
        ensureCollection();
        String expr = libraryId != null ? "library_id == " + libraryId : null;
        SearchParam.Builder builder = SearchParam.newBuilder()
                .withCollectionName(collectionName())
                .withMetricType(MetricType.IP)
                .withTopK(Math.max(1, topK))
                .withVectors(Collections.singletonList(toList(embedding)))
                .withVectorFieldName("embedding")
                .withParams("{\"nprobe\":16}")
                .withOutFields(List.of("library_id", "face_entry_id", "label", "person_name", "person_code"));
        if (expr != null) {
            builder.withExpr(expr);
        }
        R<SearchResults> result = client.search(builder.build());
        if (result.getStatus() != R.Status.Success.getCode()) {
            throw new IllegalStateException("Milvus search failed: " + result.getMessage());
        }
        SearchResultsWrapper wrapper = new SearchResultsWrapper(result.getData().getResults());
        List<Map<String, Object>> items = new ArrayList<>();
        List<SearchResultsWrapper.IDScore> scores = wrapper.getIDScore(0);
        for (SearchResultsWrapper.IDScore score : scores) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("milvus_id", String.valueOf(score.getLongID()));
            row.put("similarity", (double) score.getScore());
            row.put("library_id", score.get("library_id"));
            row.put("face_entry_id", score.get("face_entry_id"));
            row.put("label", score.get("label"));
            row.put("person_name", score.get("person_name"));
            row.put("person_code", score.get("person_code"));
            items.add(row);
        }
        return items;
    }

    private void ensureClient() {
        if (client != null) {
            return;
        }
        synchronized (lock) {
            if (client != null) {
                return;
            }
            HostPort hp = parseUri(milvusUri());
            client = new MilvusServiceClient(ConnectParam.newBuilder()
                    .withHost(hp.host)
                    .withPort(hp.port)
                    .build());
            log.info("Milvus client connected: {}:{}", hp.host, hp.port);
        }
    }

    private void ensureCollection() {
        ensureClient();
        if (collectionReady) {
            return;
        }
        synchronized (lock) {
            if (collectionReady) {
                return;
            }
            R<Boolean> has = client.hasCollection(HasCollectionParam.newBuilder()
                    .withCollectionName(collectionName())
                    .build());
            if (has.getStatus() != R.Status.Success.getCode()) {
                throw new IllegalStateException("Milvus hasCollection failed: " + has.getMessage());
            }
            if (!Boolean.TRUE.equals(has.getData())) {
                List<FieldType> fields = List.of(
                        FieldType.newBuilder().withName("id").withDataType(DataType.Int64)
                                .withPrimaryKey(true).withAutoID(true).build(),
                        FieldType.newBuilder().withName("library_id").withDataType(DataType.Int64).build(),
                        FieldType.newBuilder().withName("face_entry_id").withDataType(DataType.Int64).build(),
                        FieldType.newBuilder().withName("label").withDataType(DataType.VarChar)
                                .withMaxLength(256).build(),
                        FieldType.newBuilder().withName("person_name").withDataType(DataType.VarChar)
                                .withMaxLength(256).build(),
                        FieldType.newBuilder().withName("person_code").withDataType(DataType.VarChar)
                                .withMaxLength(128).build(),
                        FieldType.newBuilder().withName("embedding").withDataType(DataType.FloatVector)
                                .withDimension(DIM).build()
                );
                R<RpcStatus> created = client.createCollection(CreateCollectionParam.newBuilder()
                        .withCollectionName(collectionName())
                        .withDescription("face embeddings")
                        .withFieldTypes(fields)
                        .build());
                if (created.getStatus() != R.Status.Success.getCode()) {
                    throw new IllegalStateException("createCollection failed: " + created.getMessage());
                }
                client.createIndex(CreateIndexParam.newBuilder()
                        .withCollectionName(collectionName())
                        .withFieldName("embedding")
                        .withIndexType(IndexType.IVF_FLAT)
                        .withMetricType(MetricType.IP)
                        .withExtraParam("{\"nlist\":128}")
                        .build());
            }
            client.loadCollection(LoadCollectionParam.newBuilder()
                    .withCollectionName(collectionName())
                    .build());
            collectionReady = true;
        }
    }

    private static List<Float> toList(float[] embedding) {
        List<Float> list = new ArrayList<>(embedding.length);
        for (float v : embedding) {
            list.add(v);
        }
        return list;
    }

    private static String nullToEmpty(String s) {
        return s == null ? "" : s;
    }

    private static HostPort parseUri(String uri) {
        String raw = uri == null ? "http://127.0.0.1:19530" : uri.trim();
        raw = raw.replace("http://", "").replace("https://", "");
        String host = raw;
        int port = 19530;
        int idx = raw.lastIndexOf(':');
        if (idx > 0) {
            host = raw.substring(0, idx);
            try {
                port = Integer.parseInt(raw.substring(idx + 1));
            } catch (NumberFormatException ignored) {
                port = 19530;
            }
        }
        return new HostPort(host, port);
    }

    @PreDestroy
    public void close() {
        if (!closed.compareAndSet(false, true)) {
            return;
        }
        synchronized (lock) {
            if (client != null) {
                try {
                    client.close();
                } catch (Exception ignored) {
                }
                client = null;
            }
            collectionReady = false;
        }
    }

    private record HostPort(String host, int port) {
    }
}
