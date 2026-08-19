package com.basiclab.iot.node.util;

import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class RemotePortCheckUtil {

    private static final Pattern PORT_LINE = Pattern.compile("^PORT:(\\d+):(FREE|OCCUPIED)(?::(.*))?$");

    private RemotePortCheckUtil() {
    }

    public static LinkedHashMap<String, Integer> mediaDeployPorts(Map<String, String> tags) {
        LinkedHashMap<String, Integer> ports = new LinkedHashMap<>();
        ports.put("SRS RTMP", MediaStackDeployUtil.tagInt(tags, "srs_rtmp_port", 1935));
        ports.put("SRS HTTP", MediaStackDeployUtil.tagInt(tags, "srs_http_port", 8080));
        ports.put("SRS API", MediaStackDeployUtil.tagInt(tags, "srs_api_port", 1985));
        ports.put("SRS WebRTC", MediaStackDeployUtil.tagInt(tags, "srs_rtc_port", 8000));
        ports.put("ZLM HTTP", MediaStackDeployUtil.tagInt(tags, "zlm_http_port", 6080));
        ports.put("ZLM RTMP", MediaStackDeployUtil.tagInt(tags, "zlm_rtmp_port", 10935));
        ports.put("ZLM RTSP", MediaStackDeployUtil.tagInt(tags, "zlm_rtsp_port", 8554));
        ports.put("ZLM WebRTC", MediaStackDeployUtil.tagInt(tags, "zlm_rtc_port", 8800));
        return ports;
    }

    public static LinkedHashMap<String, Integer> mqttDeployPorts(Map<String, String> tags) {
        LinkedHashMap<String, Integer> ports = new LinkedHashMap<>();
        ports.put("MQTT TCP", MqttStackDeployUtil.tagInt(tags, "mqtt_tcp_port", 1883));
        ports.put("MQTT SSL", MqttStackDeployUtil.tagInt(tags, "mqtt_ssl_port", 8883));
        ports.put("MQTT WS", MqttStackDeployUtil.tagInt(tags, "mqtt_ws_port", 8083));
        ports.put("MQTT WSS", MqttStackDeployUtil.tagInt(tags, "mqtt_wss_port", 8084));
        ports.put("EMQX Dashboard", MqttStackDeployUtil.tagInt(tags, "emqx_dashboard_port", 18083));
        return ports;
    }

    public static NodePortCheckRespVO checkPorts(SshSessionHelper ssh, LinkedHashMap<String, Integer> portMap)
            throws Exception {
        NodePortCheckRespVO resp = new NodePortCheckRespVO();
        List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
        resp.setSteps(steps);

        if (portMap == null || portMap.isEmpty()) {
            resp.setSuccess(true);
            resp.setPortsReady(true);
            resp.setMessage("无需检测端口");
            return resp;
        }

        String script = buildPortCheckScript(portMap.values());
        SshSessionHelper.SshExecResult result = ssh.exec(script, 60000);
        List<PortProbe> probes = parsePortOutput(result.combinedOutput(), portMap);

        List<NodePortCheckRespVO.PortItem> items = new ArrayList<>();
        int blockedCount = 0;
        int allowedOccupiedCount = 0;
        StringBuilder stepOutput = new StringBuilder();

        for (PortProbe probe : probes) {
            boolean allowed = probe.occupied && isAllowedOccupation(probe.label, probe.processInfo);
            String status = probe.occupied ? (allowed ? "allowed" : "occupied") : "free";

            NodePortCheckRespVO.PortItem item = new NodePortCheckRespVO.PortItem();
            item.setName(probe.label);
            item.setPort(probe.port);
            item.setStatus(status);
            if (probe.occupied && probe.processInfo != null && !probe.processInfo.isBlank()) {
                item.setProcess(trimProcessInfo(probe.processInfo));
            }
            items.add(item);

            stepOutput.append(formatPortLine(item)).append('\n');
            if ("occupied".equals(status)) {
                blockedCount++;
            } else if ("allowed".equals(status)) {
                allowedOccupiedCount++;
            }
        }

        resp.setPorts(items);
        boolean portsReady = blockedCount == 0;
        resp.setPortsReady(portsReady);
        resp.setSuccess(result.isSuccess() || !probes.isEmpty());
        resp.setMessage(buildSummaryMessage(portMap.size(), blockedCount, allowedOccupiedCount, portsReady));

        NodeMediaRemoteDeployRespVO.DeployStep step = new NodeMediaRemoteDeployRespVO.DeployStep();
        step.setName("端口占用检测");
        step.setOutput(stepOutput.toString().trim());
        step.setStatus(portsReady ? "success" : "failed");
        steps.add(step);

        if (!result.isSuccess() && probes.isEmpty()) {
            resp.setSuccess(false);
            resp.setPortsReady(false);
            resp.setMessage("端口检测命令执行失败");
            step.setStatus("failed");
            step.setOutput(trimOutput(result.combinedOutput(), 2000));
        }
        return resp;
    }

    private static String buildPortCheckScript(Iterable<Integer> ports) {
        StringBuilder sb = new StringBuilder();
        sb.append("#!/usr/bin/env bash\n");
        sb.append("set -uo pipefail\n");
        sb.append("check_port() {\n");
        sb.append("  local port=\"$1\"\n");
        sb.append("  local line=\"\"\n");
        sb.append("  if command -v ss >/dev/null 2>&1; then\n");
        sb.append("    line=$(ss -tlnp 2>/dev/null | grep -E \"[:.]${port}[[:space:]]\" | head -1 || true)\n");
        sb.append("  elif command -v netstat >/dev/null 2>&1; then\n");
        sb.append("    line=$(netstat -tlnp 2>/dev/null | grep -E \"[:.]${port}[[:space:]]\" | head -1 || true)\n");
        sb.append("  fi\n");
        sb.append("  if [ -z \"${line}\" ]; then\n");
        sb.append("    echo \"PORT:${port}:FREE\"\n");
        sb.append("    return\n");
        sb.append("  fi\n");
        sb.append("  owner=\"\"\n");
        sb.append("  if command -v docker >/dev/null 2>&1; then\n");
        sb.append("    owner=$(docker ps --format '{{.Names}} {{.Ports}}' 2>/dev/null "
                + "| grep -E \":${port}->\" | head -1 || true)\n");
        sb.append("  fi\n");
        sb.append("  if [ -n \"${owner}\" ]; then\n");
        sb.append("    echo \"PORT:${port}:OCCUPIED:${owner}\"\n");
        sb.append("  else\n");
        sb.append("    echo \"PORT:${port}:OCCUPIED:${line}\"\n");
        sb.append("  fi\n");
        sb.append("}\n");
        for (Integer port : ports) {
            sb.append("check_port ").append(port).append('\n');
        }
        return sb.toString();
    }

    private static List<PortProbe> parsePortOutput(String output, LinkedHashMap<String, Integer> portMap) {
        Map<Integer, PortProbe> byPort = new LinkedHashMap<>();
        for (Map.Entry<String, Integer> entry : portMap.entrySet()) {
            PortProbe probe = new PortProbe();
            probe.label = entry.getKey();
            probe.port = entry.getValue();
            byPort.put(probe.port, probe);
        }

        if (output == null) {
            return new ArrayList<>(byPort.values());
        }
        for (String line : output.split("\n")) {
            Matcher matcher = PORT_LINE.matcher(line.trim());
            if (!matcher.matches()) {
                continue;
            }
            int port = Integer.parseInt(matcher.group(1));
            PortProbe probe = byPort.get(port);
            if (probe == null) {
                continue;
            }
            probe.occupied = "OCCUPIED".equals(matcher.group(2));
            if (matcher.group(3) != null) {
                probe.processInfo = matcher.group(3).trim();
            }
        }
        return new ArrayList<>(byPort.values());
    }

    private static boolean isAllowedOccupation(String label, String processInfo) {
        if (processInfo == null || processInfo.isBlank()) {
            return false;
        }
        String lower = processInfo.toLowerCase(Locale.ROOT);
        if (label.startsWith("SRS")) {
            return lower.contains("-srs")
                    || lower.contains("ossrs")
                    || lower.contains("/srs")
                    || lower.contains("srs:");
        }
        if (label.startsWith("ZLM")) {
            return lower.contains("-zlm")
                    || lower.contains("mediaserver")
                    || lower.contains("zlmediakit")
                    || lower.contains("zlm:");
        }
        if (label.contains("Agent") || label.contains("代理")) {
            return lower.contains("easyaiot-node-agent")
                    || lower.contains("run_agent")
                    || lower.contains("agent_server")
                    || lower.contains("node-agent");
        }
        if (label.startsWith("MQTT") || label.startsWith("EMQX")) {
            return lower.contains("emqx")
                    || lower.contains("-emqx")
                    || lower.contains("beam.smp");
        }
        return false;
    }

    private static String formatPortLine(NodePortCheckRespVO.PortItem item) {
        String statusText = switch (item.getStatus()) {
            case "free" -> "空闲";
            case "allowed" -> "已占用（本平台服务）";
            default -> "已占用（冲突）";
        };
        String line = item.getName() + " " + item.getPort() + "：" + statusText;
        if (item.getProcess() != null && !item.getProcess().isBlank()) {
            line += " — " + item.getProcess();
        }
        return line;
    }

    private static String buildSummaryMessage(int total, int blocked, int allowedOccupied, boolean portsReady) {
        if (portsReady) {
            if (allowedOccupied > 0) {
                return "部署端口检测通过：" + allowedOccupied + " 个端口已被本平台服务占用，"
                        + (total - allowedOccupied) + " 个端口空闲";
            }
            return "部署端口均空闲，可以部署";
        }
        return blocked + " 个部署端口被其他进程占用，请释放冲突端口或修改节点端口配置后再部署";
    }

    private static String trimProcessInfo(String info) {
        String trimmed = info.trim();
        if (trimmed.length() <= 200) {
            return trimmed;
        }
        return trimmed.substring(0, 200) + "...";
    }

    private static String trimOutput(String text, int maxLen) {
        if (text == null) {
            return "";
        }
        String trimmed = text.trim();
        if (trimmed.length() <= maxLen) {
            return trimmed;
        }
        return trimmed.substring(0, maxLen) + "\n... (输出已截断)";
    }

    private static final class PortProbe {
        private String label;
        private int port;
        private boolean occupied;
        private String processInfo;
    }

}
