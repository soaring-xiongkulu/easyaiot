package com.basiclab.iot.node.framework.bootstrap;

import com.basiclab.iot.node.service.ComputeNodeService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.TimeUnit;

/**
 * 启动时自动纳管控制面宿主机节点，并异步触发宿主机 Agent 凭据同步。
 */
@Slf4j
@Component
public class PlatformNodeBootstrap implements ApplicationRunner {

    @Resource
    private ComputeNodeService computeNodeService;

    @Override
    public void run(ApplicationArguments args) {
        try {
            computeNodeService.ensurePlatformNode();
        } catch (Exception ex) {
            log.warn("控制面节点自动纳管失败: {}", ex.getMessage());
        }
        triggerPlatformAgentSyncAsync();
    }

    private void triggerPlatformAgentSyncAsync() {
        if ("1".equals(System.getenv("EASYAIOT_SKIP_PLATFORM_AGENT_SYNC"))) {
            return;
        }
        String script = System.getenv("EASYAIOT_PLATFORM_AGENT_SYNC_SCRIPT");
        if (script == null || script.isBlank()) {
            script = resolveSyncScript();
        }
        if (script == null) {
            return;
        }
        Path scriptPath = Paths.get(script);
        if (!Files.isRegularFile(scriptPath)) {
            log.debug("未找到控制面 Agent 同步脚本: {}", script);
            return;
        }
        String resolved = scriptPath.toAbsolutePath().toString();
        Thread syncThread = new Thread(() -> {
            try {
                log.info("iot-node 已就绪，触发宿主机 Agent 凭据同步: {}", resolved);
                Process process = new ProcessBuilder("bash", resolved)
                        .redirectErrorStream(true)
                        .start();
                if (!process.waitFor(3, TimeUnit.MINUTES)) {
                    process.destroyForcibly();
                    log.warn("控制面 Agent 同步脚本超时: {}", resolved);
                }
            } catch (Exception ex) {
                log.warn("控制面 Agent 同步脚本执行失败: {}", ex.getMessage());
            }
        }, "platform-agent-sync");
        syncThread.setDaemon(true);
        syncThread.start();
    }

    private String resolveSyncScript() {
        String envRoot = System.getenv("EASYAIOT_ROOT");
        if (envRoot != null && !envRoot.isBlank()) {
            Path candidate = Paths.get(envRoot, ".scripts/node/ensure_platform_agent.sh");
            if (Files.isRegularFile(candidate)) {
                return candidate.toString();
            }
        }
        Path current = Paths.get(System.getProperty("user.dir", ".")).toAbsolutePath();
        for (int depth = 0; depth < 8 && current != null; depth++) {
            Path candidate = current.resolve(".scripts/node/ensure_platform_agent.sh");
            if (Files.isRegularFile(candidate)) {
                return candidate.toString();
            }
            current = current.getParent();
        }
        return null;
    }
}
