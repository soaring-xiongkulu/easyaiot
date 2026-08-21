package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeSentinelSnapshotDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSentinelSnapshotMapper;
import com.basiclab.iot.node.domain.vo.NodeSentinelProbeReqVO;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.NodeSentinelService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * 控制面兜底巡检：节点在线但 Sentinel 快照过期时，主动触发 L1 探测。
 * 主路径仍是各节点 Sentinel 经网关心跳上报。
 */
@Component
@Slf4j
public class SentinelProbeScheduler {

    private static final String LOCK_KEY = "easyaiot:sentinel:probe-stale-lock";

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeSentinelSnapshotMapper nodeSentinelSnapshotMapper;
    @Resource
    private NodeSentinelService nodeSentinelService;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Value("${easyaiot.sentinel.enabled:true}")
    private boolean sentinelEnabled;
    @Value("${easyaiot.sentinel.probe-stale-enabled:true}")
    private boolean probeStaleEnabled;
    @Value("${easyaiot.sentinel.fresh-seconds:90}")
    private long freshSeconds;

    private final AtomicBoolean localRunning = new AtomicBoolean(false);

    @Scheduled(fixedDelayString = "${easyaiot.sentinel.probe-stale-interval-ms:180000}")
    public void probeStaleNodes() {
        if (!sentinelEnabled || !probeStaleEnabled) {
            return;
        }
        if (!localRunning.compareAndSet(false, true)) {
            return;
        }
        Boolean locked = null;
        try {
            locked = stringRedisTemplate.opsForValue().setIfAbsent(LOCK_KEY, "1", 3, TimeUnit.MINUTES);
            if (Boolean.FALSE.equals(locked)) {
                return;
            }
            List<ComputeNodeDO> nodes = computeNodeMapper.selectList();
            LocalDateTime staleBefore = LocalDateTime.now().minusSeconds(Math.max(freshSeconds * 2, 180));
            for (ComputeNodeDO node : nodes) {
                if (node == null || node.getId() == null) {
                    continue;
                }
                if (ComputeNodeServiceImpl.isPlatformNode(node)) {
                    continue;
                }
                if (!NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
                    continue;
                }
                NodeSentinelSnapshotDO snapshot = nodeSentinelSnapshotMapper.selectById(node.getId());
                if (snapshot != null && snapshot.getLastProbeAt() != null
                        && snapshot.getLastProbeAt().isAfter(staleBefore)) {
                    continue;
                }
                try {
                    NodeSentinelProbeReqVO req = new NodeSentinelProbeReqVO();
                    req.setNodeId(node.getId());
                    req.setLevel("L1");
                    nodeSentinelService.probe(req);
                } catch (Exception e) {
                    log.debug("Sentinel 兜底探测跳过 nodeId={}: {}", node.getId(), e.getMessage());
                }
            }
        } finally {
            if (Boolean.TRUE.equals(locked)) {
                stringRedisTemplate.delete(LOCK_KEY);
            }
            localRunning.set(false);
        }
    }
}
