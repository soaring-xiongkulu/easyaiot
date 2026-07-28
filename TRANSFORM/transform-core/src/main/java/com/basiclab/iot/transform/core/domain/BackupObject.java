package com.basiclab.iot.transform.core.domain;
import lombok.*; import java.time.Instant;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class BackupObject { private String eventId; private String path; private Instant createdAt; }
