package com.basiclab.iot.transform.core.domain;
import lombok.*; import java.time.Instant; import java.util.*;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class Party { private String id; private String name; private String type; private boolean enabled; @Builder.Default private Map<String,Object> config=new HashMap<>(); private Instant createdAt; }
