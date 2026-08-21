package com.basiclab.iot.node.service;

/**
 * 控制面 / Gateway 接入地址解析（Hook 回调、Agent 注册等）。
 * <p>
 * 优先级：显式 control-plane-url → 非回环 hook-host → 平台节点 host → 宿主机 IP 探测 → 配置默认。
 */
public interface ControlPlaneEndpointResolver {

    /** SRS/ZLM Hook 回调目标 host（计算节点须能访问，非 127.0.0.1）。 */
    String resolveHookHost();

    /** Gateway / Hook 端口，默认 48080。 */
    int resolveHookPort();

    /** Hook 路径前缀：经 Gateway 为 /admin-api，直连 VIDEO 为空。 */
    String resolveHookPathPrefix();

    /** Agent 控制面根 URL，如 http://10.x.x.x:48080/admin-api/node/agent */
    String resolveControlPlaneUrl(String override);
}
