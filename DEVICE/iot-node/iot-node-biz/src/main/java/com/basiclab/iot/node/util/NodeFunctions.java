package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.enums.NodeFunctionEnum;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * 节点功能开关：node_role 列存 CSV，capabilities 由功能推导。
 */
public final class NodeFunctions {

    public static final List<String> ALL_IDS;
    public static final List<String> PLATFORM_DEFAULT = List.of(
            NodeFunctionEnum.ALGORITHM.getId(),
            NodeFunctionEnum.FORWARD.getId(),
            NodeFunctionEnum.LIVE.getId(),
            NodeFunctionEnum.LABEL.getId(),
            NodeFunctionEnum.INFER.getId(),
            NodeFunctionEnum.NFS.getId());
    public static final List<String> NFS_CLIENT = List.of(
            NodeFunctionEnum.ALGORITHM.getId(),
            NodeFunctionEnum.TRAIN.getId(),
            NodeFunctionEnum.LABEL.getId(),
            NodeFunctionEnum.INFER.getId());

    private static final Map<String, List<String>> CAPABILITY_MAP = new LinkedHashMap<>();
    private static final Map<String, List<String>> WORKLOAD_MAP = new LinkedHashMap<>();
    /** 历史单角色 → 功能列表（旧版控制面常用 hybrid） */
    private static final Map<String, List<String>> LEGACY_ROLE_MAP = new LinkedHashMap<>();

    static {
        List<String> ids = new ArrayList<>();
        for (NodeFunctionEnum value : NodeFunctionEnum.values()) {
            ids.add(value.getId());
        }
        ALL_IDS = Collections.unmodifiableList(ids);

        LEGACY_ROLE_MAP.put("hybrid", PLATFORM_DEFAULT);
        LEGACY_ROLE_MAP.put("compute", List.of(
                NodeFunctionEnum.ALGORITHM.getId(), NodeFunctionEnum.INFER.getId()));
        LEGACY_ROLE_MAP.put("gpu", List.of(
                NodeFunctionEnum.ALGORITHM.getId(), NodeFunctionEnum.TRAIN.getId(), NodeFunctionEnum.LLM.getId()));
        LEGACY_ROLE_MAP.put("media", List.of(
                NodeFunctionEnum.LIVE.getId(), NodeFunctionEnum.FORWARD.getId()));
        LEGACY_ROLE_MAP.put("edge", List.of(
                NodeFunctionEnum.ALGORITHM.getId(), NodeFunctionEnum.FORWARD.getId(), NodeFunctionEnum.LIVE.getId()));

        CAPABILITY_MAP.put("algorithm", List.of("algorithm_realtime", "algorithm_snap", "algorithm_patrol"));
        CAPABILITY_MAP.put("forward", List.of("stream_forward"));
        CAPABILITY_MAP.put("live", List.of("srs_live", "srs_ai", "zlm"));
        CAPABILITY_MAP.put("train", List.of("model_train"));
        CAPABILITY_MAP.put("llm", List.of("llm_inference"));
        CAPABILITY_MAP.put("label", List.of("auto_label"));
        CAPABILITY_MAP.put("infer", List.of("ai_inference"));
        CAPABILITY_MAP.put("mqtt", List.of("emqx", "mqtt_gateway"));
        CAPABILITY_MAP.put("nfs", List.of("nfs_server", "media_storage"));
        CAPABILITY_MAP.put("transform", List.of("transform_runtime"));

        WORKLOAD_MAP.put("algorithm_task", List.of("algorithm"));
        WORKLOAD_MAP.put("stream_forward", List.of("forward"));
        WORKLOAD_MAP.put("srs_live", List.of("live"));
        WORKLOAD_MAP.put("srs_ai", List.of("live"));
        WORKLOAD_MAP.put("zlm", List.of("live"));
        WORKLOAD_MAP.put("model_train", List.of("train"));
        WORKLOAD_MAP.put("llm_service", List.of("llm"));
        WORKLOAD_MAP.put("auto_label", List.of("label"));
        WORKLOAD_MAP.put("ai_service", List.of("infer"));
        WORKLOAD_MAP.put("emqx", List.of("mqtt"));
        WORKLOAD_MAP.put("mqtt_gateway", List.of("mqtt"));
        WORKLOAD_MAP.put("transform_runtime", List.of("transform"));
        WORKLOAD_MAP.put("post_process", List.of("algorithm", "infer"));
    }

    private NodeFunctions() {
    }

    public static boolean isLegacyRole(String role) {
        if (StrUtil.isBlank(role)) {
            return false;
        }
        String key = role.trim().toLowerCase(Locale.ROOT);
        return LEGACY_ROLE_MAP.containsKey(key);
    }

    public static List<String> parse(String csv) {
        if (StrUtil.isBlank(csv)) {
            return Collections.emptyList();
        }
        String trimmed = csv.trim();
        List<String> legacy = LEGACY_ROLE_MAP.get(trimmed.toLowerCase(Locale.ROOT));
        if (legacy != null) {
            return new ArrayList<>(legacy);
        }
        LinkedHashSet<String> set = new LinkedHashSet<>();
        for (String part : trimmed.split("[,\\s]+")) {
            NodeFunctionEnum fn = NodeFunctionEnum.of(part);
            if (fn != null) {
                set.add(fn.getId());
            }
        }
        return new ArrayList<>(set);
    }

    public static List<String> parse(ComputeNodeDO node) {
        return node == null ? Collections.emptyList() : parse(node.getNodeRole());
    }

    public static List<String> normalize(List<String> functions) {
        if (functions == null || functions.isEmpty()) {
            return Collections.emptyList();
        }
        LinkedHashSet<String> set = new LinkedHashSet<>();
        for (String raw : functions) {
            NodeFunctionEnum fn = NodeFunctionEnum.of(raw);
            if (fn != null) {
                set.add(fn.getId());
            }
        }
        return new ArrayList<>(set);
    }

    public static List<String> withPlatformDefaults(String existingRole) {
        LinkedHashSet<String> functions = new LinkedHashSet<>(PLATFORM_DEFAULT);
        functions.addAll(parse(existingRole));
        return new ArrayList<>(functions);
    }

    public static String toCsv(List<String> functions) {
        List<String> normalized = normalize(functions);
        return String.join(",", normalized);
    }

    public static boolean has(ComputeNodeDO node, String functionId) {
        return parse(node).contains(functionId == null ? "" : functionId.trim().toLowerCase(Locale.ROOT));
    }

    public static boolean hasAny(ComputeNodeDO node, String... functionIds) {
        List<String> parsed = parse(node);
        if (parsed.isEmpty() || functionIds == null) {
            return false;
        }
        for (String id : functionIds) {
            if (parsed.contains(id)) {
                return true;
            }
        }
        return false;
    }

    public static boolean isNfsServer(ComputeNodeDO node) {
        return has(node, NodeFunctionEnum.NFS.getId());
    }

    public static boolean isNfsClient(ComputeNodeDO node) {
        return hasAny(node, NFS_CLIENT.toArray(new String[0]));
    }

    public static boolean isLive(ComputeNodeDO node) {
        return hasAny(node, NodeFunctionEnum.LIVE.getId(), NodeFunctionEnum.FORWARD.getId());
    }

    public static boolean isMqtt(ComputeNodeDO node) {
        return has(node, NodeFunctionEnum.MQTT.getId());
    }

    public static boolean requiresGpu(List<String> functions) {
        List<String> normalized = normalize(functions);
        return normalized.contains(NodeFunctionEnum.TRAIN.getId())
                || normalized.contains(NodeFunctionEnum.LLM.getId());
    }

    public static boolean isComputeWorkloadNode(ComputeNodeDO node) {
        return hasAny(node,
                NodeFunctionEnum.ALGORITHM.getId(),
                NodeFunctionEnum.FORWARD.getId(),
                NodeFunctionEnum.TRAIN.getId(),
                NodeFunctionEnum.LLM.getId(),
                NodeFunctionEnum.LABEL.getId(),
                NodeFunctionEnum.INFER.getId(),
                NodeFunctionEnum.TRANSFORM.getId());
    }

    public static Map<String, Boolean> capabilities(List<String> functions) {
        Map<String, Boolean> caps = new LinkedHashMap<>();
        for (String fn : normalize(functions)) {
            List<String> keys = CAPABILITY_MAP.getOrDefault(fn, Collections.emptyList());
            for (String key : keys) {
                caps.put(key, true);
            }
        }
        return caps;
    }

    public static Map<String, Boolean> capabilities(ComputeNodeDO node) {
        return capabilities(parse(node));
    }

    public static boolean matchesWorkload(ComputeNodeDO node, String workloadType) {
        if (StrUtil.isBlank(workloadType)) {
            return true;
        }
        List<String> required = WORKLOAD_MAP.get(workloadType);
        if (required == null || required.isEmpty()) {
            return isComputeWorkloadNode(node);
        }
        return hasAny(node, required.toArray(new String[0]));
    }

    public static Set<String> declaredCapabilityKeys(ComputeNodeDO node) {
        return capabilities(node).keySet();
    }
}
