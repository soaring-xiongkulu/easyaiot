package com.basiclab.iot.transform.core.domain;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope; import lombok.*; import java.time.Instant;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class OutboxRecord { private String id; private String eventId; private String partyId; private String contractId; private String channel; private String status; private int attempts; private String error; private TransformEnvelope envelope; private Instant createdAt; private Instant updatedAt; }
