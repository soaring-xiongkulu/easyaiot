package com.basiclab.iot.transform.core.domain;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope; import lombok.*; import java.time.Instant;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class DlqRecord { private String id; private String source; private String reason; private String outboxId; private TransformEnvelope envelope; private Instant createdAt; }
