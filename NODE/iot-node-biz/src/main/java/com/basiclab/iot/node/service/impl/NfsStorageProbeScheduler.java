package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.service.NodeStorageService;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshReqVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * NFS 共享媒体定时巡检：复用 batchRefreshBySsh 写回 tags / op_log。
 */
@Component
@Slf4j
public class NfsStorageProbeScheduler {

    private static final String LOCK_KEY = "easyaiot:storage:nfs-probe-lock";

    @Resource
    private NodeStorageService nodeStorageService;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Value("${easyaiot.storage.nfs-probe-enabled:true}")
    private boolean probeEnabled;

    private final AtomicBoolean localRunning = new AtomicBoolean(false);

    @Scheduled(fixedDelayString = "${easyaiot.storage.nfs-probe-interval-ms:900000}")
    public void autoProbe() {
        if (!probeEnabled) {
            return;
        }
        if (!localRunning.compareAndSet(false, true)) {
            log.info("[NfsStorageProbeScheduler] 上一轮仍在执行，跳过");
            return;
        }
        Boolean locked = null;
        try {
            locked = stringRedisTemplate.opsForValue().setIfAbsent(LOCK_KEY, "1", 20, TimeUnit.MINUTES);
            if (Boolean.FALSE.equals(locked)) {
                log.info("[NfsStorageProbeScheduler] 其他实例持有锁，跳过");
                return;
            }
            NodeNfsBatchRefreshReqVO req = new NodeNfsBatchRefreshReqVO();
            req.setAuto(true);
            var resp = nodeStorageService.batchRefreshBySsh(req);
            log.info("[NfsStorageProbeScheduler] 巡检完成: {}", resp != null ? resp.getMessage() : "null");
        } catch (Exception e) {
            log.warn("[NfsStorageProbeScheduler] 巡检失败: {}", e.getMessage());
        } finally {
            try {
                if (Boolean.TRUE.equals(locked)) {
                    stringRedisTemplate.delete(LOCK_KEY);
                }
            } catch (Exception ignore) {
                // ignore
            }
            localRunning.set(false);
        }
    }
}
