package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.enums.NodeRoleEnum;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * MQTT 网关（EMQX）远程部署环境变量与脚本构建。
 */
public final class MqttStackDeployUtil {

    private static final String REMOTE_ROOT = "/opt/easyaiot/mqtt-cluster";
    public static final String DEFAULT_COOKIE = "emqxsecretcookie";
    public static final String DEFAULT_DASHBOARD_USER = "admin";
    public static final String DEFAULT_DASHBOARD_PASSWORD = "basiclab@iot6874125784";

    private MqttStackDeployUtil() {
    }

    public static String remoteClusterRoot() {
        return REMOTE_ROOT;
    }

    public static boolean isMqttRole(String role) {
        return NodeRoleEnum.MQTT.getRole().equals(role);
    }

    public static String sanitizeNodeName(String name, String host) {
        String raw = StrUtil.blankToDefault(name, StrUtil.blankToDefault(host, "mqtt-node")).trim().toLowerCase(Locale.ROOT);
        String slug = raw.replaceAll("[^a-z0-9-]+", "-").replaceAll("^-+|-+$", "");
        return StrUtil.isBlank(slug) ? "mqtt-node" : slug;
    }

    public static int tagInt(Map<String, String> tags, String key, int defaultValue) {
        if (tags == null || !tags.containsKey(key)) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(tags.get(key));
        } catch (NumberFormatException ignored) {
            return defaultValue;
        }
    }

    public static String tagString(Map<String, String> tags, String key, String defaultValue) {
        if (tags == null || !tags.containsKey(key)) {
            return defaultValue;
        }
        String val = tags.get(key);
        return StrUtil.isBlank(val) ? defaultValue : val;
    }

    public enum DeployPhase {
        FULL,
        PREPARE_IMAGES,
        DEPLOY_SERVICES
    }

    public static String buildDeployScript(ComputeNodeDO node, String authHost, int authPort) {
        return buildDeployScript(node, authHost, authPort, DeployPhase.FULL);
    }

    public static String buildDeployScript(ComputeNodeDO node, String authHost, int authPort, DeployPhase phase) {
        StringBuilder sb = new StringBuilder(buildDeployEnvScript(node, authHost, authPort));
        if (phase == DeployPhase.PREPARE_IMAGES) {
            sb.append("export MQTT_PREPARE_IMAGES_ONLY=1\n");
        } else if (phase == DeployPhase.DEPLOY_SERVICES) {
            sb.append("export MQTT_DEPLOY_SERVICES_ONLY=1\n");
        }
        sb.append("bash \"${MQTT_CLUSTER_ROOT}/install_mqtt_stack.sh\"\n");
        return sb.toString();
    }

    public static Map<String, String> buildDeployEnvMap(ComputeNodeDO node, String authHost, int authPort) {
        Map<String, String> tags = node.getTags();
        String nodeName = sanitizeNodeName(node.getName(), node.getHost());
        String host = node.getHost();
        int mqttTcp = tagInt(tags, "mqtt_tcp_port", 1883);
        int mqttSsl = tagInt(tags, "mqtt_ssl_port", 8883);
        int mqttWs = tagInt(tags, "mqtt_ws_port", 8083);
        int mqttWss = tagInt(tags, "mqtt_wss_port", 8084);
        int dashboard = tagInt(tags, "emqx_dashboard_port", 18083);
        String cookie = tagString(tags, "emqx_cookie", DEFAULT_COOKIE);
        String seeds = tagString(tags, "emqx_cluster_seeds", "");
        String authPath = tagString(tags, "mqtt_auth_path", "/mqtt/auth");
        int resolvedAuthPort = tagInt(tags, "mqtt_auth_port", authPort);
        String resolvedAuthHost = tagString(tags, "mqtt_auth_host", authHost);

        Map<String, String> env = new LinkedHashMap<>();
        env.put("MQTT_CLUSTER_ROOT", REMOTE_ROOT);
        env.put("MQTT_NODE_NAME", nodeName);
        env.put("MQTT_NODE_HOST", host);
        env.put("MQTT_AUTH_HOST", resolvedAuthHost);
        env.put("MQTT_AUTH_PORT", String.valueOf(resolvedAuthPort));
        env.put("MQTT_AUTH_PATH", authPath);
        env.put("MQTT_TCP_PORT", String.valueOf(mqttTcp));
        env.put("MQTT_SSL_PORT", String.valueOf(mqttSsl));
        env.put("MQTT_WS_PORT", String.valueOf(mqttWs));
        env.put("MQTT_WSS_PORT", String.valueOf(mqttWss));
        env.put("EMQX_DASHBOARD_PORT", String.valueOf(dashboard));
        env.put("EMQX_NODE_COOKIE", cookie);
        env.put("EMQX_CLUSTER_SEEDS", seeds);
        env.put("EMQX_DASHBOARD_USER", DEFAULT_DASHBOARD_USER);
        env.put("EMQX_DASHBOARD_PASSWORD", DEFAULT_DASHBOARD_PASSWORD);
        return env;
    }

    private static String buildDeployEnvScript(ComputeNodeDO node, String authHost, int authPort) {
        Map<String, String> env = buildDeployEnvMap(node, authHost, authPort);
        StringBuilder sb = new StringBuilder("#!/usr/bin/env bash\nset -euo pipefail\n");
        for (Map.Entry<String, String> entry : env.entrySet()) {
            sb.append("export ").append(entry.getKey()).append("=\"")
                    .append(entry.getValue().replace("\"", "\\\"")).append("\"\n");
        }
        return sb.toString();
    }

}
