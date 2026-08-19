package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.service.ControlPlaneEndpointResolver;
import com.basiclab.iot.node.util.HostIpUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.net.URI;

/**
 * 自动解析控制面 Gateway 地址，避免远程节点 Hook 误配 127.0.0.1。
 */
@Slf4j
@Service
public class ControlPlaneEndpointResolverImpl implements ControlPlaneEndpointResolver {

    private static final int DEFAULT_GATEWAY_PORT = 48080;

    @Resource
    private ComputeNodeMapper computeNodeMapper;

    @Value("${easyaiot.agent.control-plane-url:}")
    private String agentControlPlaneUrl;

    @Value("${easyaiot.media.hook-host:127.0.0.1}")
    private String configuredHookHost;

    @Value("${easyaiot.media.hook-port:48080}")
    private int configuredHookPort;

    @Override
    public String resolveHookHost() {
        String fromUrl = hostFromUrl(agentControlPlaneUrl);
        if (fromUrl != null) {
            return fromUrl;
        }
        if (isReachableHost(configuredHookHost)) {
            return configuredHookHost.trim();
        }
        String platformHost = platformNodeHost();
        if (platformHost != null) {
            return platformHost;
        }
        String detected = HostIpUtil.detectHostIp();
        if (isReachableHost(detected)) {
            if (isLoopback(configuredHookHost)) {
                log.debug("媒体 Hook 使用宿主机探测 IP: {}（原配置 {}）", detected, configuredHookHost);
            }
            return detected;
        }
        return configuredHookHost != null ? configuredHookHost.trim() : "127.0.0.1";
    }

    @Override
    public int resolveHookPort() {
        Integer fromUrl = portFromUrl(agentControlPlaneUrl);
        if (fromUrl != null) {
            return fromUrl;
        }
        if (configuredHookPort > 0) {
            return configuredHookPort;
        }
        return DEFAULT_GATEWAY_PORT;
    }

    @Override
    public String resolveHookPathPrefix() {
        if (agentControlPlaneUrl != null && !agentControlPlaneUrl.isBlank()) {
            return "/admin-api";
        }
        if (isLoopback(resolveHookHost())) {
            return "";
        }
        return "/admin-api";
    }

    @Override
    public String resolveControlPlaneUrl(String override) {
        if (override != null && !override.isBlank()) {
            return override.trim().replaceAll("/+$", "");
        }
        if (agentControlPlaneUrl != null && !agentControlPlaneUrl.isBlank()) {
            return agentControlPlaneUrl.trim().replaceAll("/+$", "");
        }
        return "http://" + resolveHookHost() + ":" + resolveHookPort() + "/admin-api/node/agent";
    }

    private String platformNodeHost() {
        try {
            ComputeNodeDO node = computeNodeMapper.selectPlatformNode();
            if (node != null && isReachableHost(node.getHost())) {
                return node.getHost().trim();
            }
        } catch (Exception e) {
            log.debug("读取平台节点 host 失败: {}", e.getMessage());
        }
        return null;
    }

    private static String hostFromUrl(String url) {
        if (url == null || url.isBlank()) {
            return null;
        }
        try {
            URI uri = URI.create(url.trim());
            String host = uri.getHost();
            if (isReachableHost(host)) {
                return host.trim();
            }
        } catch (Exception ignored) {
            // fall through
        }
        return null;
    }

    private static Integer portFromUrl(String url) {
        if (url == null || url.isBlank()) {
            return null;
        }
        try {
            URI uri = URI.create(url.trim());
            if (uri.getPort() > 0) {
                return uri.getPort();
            }
            if ("https".equalsIgnoreCase(uri.getScheme())) {
                return 443;
            }
            if ("http".equalsIgnoreCase(uri.getScheme())) {
                return 80;
            }
        } catch (Exception ignored) {
            // fall through
        }
        return null;
    }

    private static boolean isLoopback(String host) {
        if (host == null) {
            return true;
        }
        String h = host.trim().toLowerCase();
        return h.isEmpty() || "127.0.0.1".equals(h) || "localhost".equals(h) || "::1".equals(h);
    }

    private static boolean isReachableHost(String host) {
        return host != null && !host.isBlank() && !isLoopback(host);
    }
}
