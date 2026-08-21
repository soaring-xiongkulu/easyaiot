package com.basiclab.iot.node.framework;

import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;
import org.springframework.util.StreamUtils;
import org.yaml.snakeyaml.Yaml;

import javax.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 加载 classpath:sentinel/*.yaml，与控制面 SENTINEL/registry 语义对齐。
 */
@Component
@Slf4j
public class SentinelCapabilityRegistry {

    private Map<String, Object> componentsRegistry = Collections.emptyMap();
    private Map<String, Object> capabilitiesRegistry = Collections.emptyMap();
    private Map<String, Object> functionsRegistry = Collections.emptyMap();

    @PostConstruct
    public void init() {
        componentsRegistry = loadYaml("sentinel/components.yaml");
        capabilitiesRegistry = loadYaml("sentinel/capabilities.yaml");
        functionsRegistry = loadYaml("sentinel/functions.yaml");
        log.info("[SentinelCapabilityRegistry] components={}, capabilities={}, functions={}",
                countTopKeys(componentsRegistry, "components"),
                countTopKeys(capabilitiesRegistry, "capabilities"),
                countTopKeys(functionsRegistry, "functions"));
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getComponents() {
        Object raw = componentsRegistry.get("components");
        if (raw instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Collections.emptyMap();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getRemediation() {
        Object raw = componentsRegistry.get("remediation");
        if (raw instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Collections.emptyMap();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getCapabilities() {
        Object raw = capabilitiesRegistry.get("capabilities");
        if (raw instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Collections.emptyMap();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getFunctions() {
        Object raw = functionsRegistry.get("functions");
        if (raw instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Collections.emptyMap();
    }

    @SuppressWarnings("unchecked")
    public List<String> platformDefaultFunctions() {
        Object raw = functionsRegistry.get("platform_default");
        if (raw instanceof List<?> list) {
            return list.stream().map(String::valueOf).toList();
        }
        return Collections.emptyList();
    }

    @SuppressWarnings("unchecked")
    public List<String> nfsClientFunctions() {
        Object raw = functionsRegistry.get("nfs_client_functions");
        if (raw instanceof List<?> list) {
            return list.stream().map(String::valueOf).toList();
        }
        return Collections.emptyList();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getAllocateDefaults() {
        Object raw = capabilitiesRegistry.get("allocate_defaults");
        if (raw instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Collections.emptyMap();
    }

    @SuppressWarnings("unchecked")
    public List<String> defaultCapabilitiesForWorkload(String workloadType) {
        if (workloadType == null || workloadType.isBlank()) {
            return Collections.emptyList();
        }
        for (Map.Entry<String, Object> entry : getCapabilities().entrySet()) {
            if (!(entry.getValue() instanceof Map<?, ?> spec)) {
                continue;
            }
            Object wt = spec.get("workload_type");
            if (workloadType.equals(String.valueOf(wt))) {
                return List.of(entry.getKey());
            }
        }
        return Collections.emptyList();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> registryView() {
        Map<String, Object> view = new HashMap<>();
        view.put("components", getComponents());
        view.put("remediation", getRemediation());
        view.put("capabilities", getCapabilities());
        view.put("allocateDefaults", getAllocateDefaults());
        view.put("functions", getFunctions());
        view.put("platformDefault", platformDefaultFunctions());
        view.put("nfsClientFunctions", nfsClientFunctions());
        return view;
    }

    private Map<String, Object> loadYaml(String path) {
        try {
            ClassPathResource resource = new ClassPathResource(path);
            if (!resource.exists()) {
                log.warn("[SentinelCapabilityRegistry] 未找到 {}", path);
                return Collections.emptyMap();
            }
            String text = StreamUtils.copyToString(resource.getInputStream(), StandardCharsets.UTF_8);
            Object loaded = new Yaml().load(text);
            if (loaded instanceof Map<?, ?> map) {
                return new HashMap<>((Map<String, Object>) map);
            }
        } catch (Exception e) {
            log.warn("[SentinelCapabilityRegistry] 加载 {} 失败: {}", path, e.getMessage());
        }
        return Collections.emptyMap();
    }

    private int countTopKeys(Map<String, Object> root, String key) {
        Object raw = root.get(key);
        if (raw instanceof Map<?, ?> map) {
            return map.size();
        }
        return 0;
    }
}
