package com.basiclab.iot.transform.runtime.service;

import com.basiclab.iot.transform.capability.map.JsonPathMapCapability;
import com.basiclab.iot.transform.capability.map.MapCapability;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.Map;

/**
 * 从 PostgreSQL MappingRule 仓储动态取规则执行映射。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Primary
@Component
@RequiredArgsConstructor
public class StoreBackedMapCapability implements MapCapability {

    private final TransformRepository repository;
    private final ObjectMapper objectMapper;

    @Override
    public TransformEnvelope map(String mappingId, TransformEnvelope source) {
        if (mappingId == null || mappingId.isBlank()) {
            return source;
        }
        var rule = repository.mapping(mappingId);
        Map<String, String> fields = rule == null || rule.getFields() == null
                ? Collections.emptyMap()
                : rule.getFields();
        return new JsonPathMapCapability(objectMapper, Map.of(mappingId, fields)).map(mappingId, source);
    }
}
