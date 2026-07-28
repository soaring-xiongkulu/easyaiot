package com.basiclab.iot.transform.core.domain;
import lombok.*; import java.time.Instant; import java.util.*;
@Data @Builder @NoArgsConstructor @AllArgsConstructor public class MappingRule { private String id; private String name; @Builder.Default private Map<String,String> fields=new LinkedHashMap<>(); private boolean enabled; private Instant createdAt; }
