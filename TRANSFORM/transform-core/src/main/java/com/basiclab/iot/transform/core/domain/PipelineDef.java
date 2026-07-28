package com.basiclab.iot.transform.core.domain;
import lombok.*; import java.time.Instant;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class PipelineDef { private String id; private String name; private String flowType; private String mappingId; private boolean enabled; private Instant createdAt; }
