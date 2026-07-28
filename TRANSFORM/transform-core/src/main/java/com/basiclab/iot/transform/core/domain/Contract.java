package com.basiclab.iot.transform.core.domain;
import lombok.*; import java.time.Instant; import java.util.*;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class Contract { private String id; private String partyId; private String flowType; private String channel; private String endpoint; private String mappingId; private boolean enabled; @Builder.Default private Map<String,Object> headers=new HashMap<>(); private Instant createdAt; }
