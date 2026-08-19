package com.basiclab.iot.node.service.impl;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.service.NodeHealthService;
import com.basiclab.iot.node.service.impl.ComputeNodeServiceImpl;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
public class NodeHealthServiceImpl implements NodeHealthService {

    private static final String HEARTBEAT_KEY_PREFIX = "node:heartbeat:";
    private static final long OFFLINE_THRESHOLD_SECONDS = 45;

    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Override
    @Scheduled(fixedDelay = 30000)
    public void checkOfflineNodes() {
        List<ComputeNodeDO> onlineNodes = computeNodeMapper.selectList(
                new LambdaQueryWrapperX<ComputeNodeDO>()
                        .eq(ComputeNodeDO::getStatus, NodeStatusEnum.ONLINE.getStatus()));
        LocalDateTime threshold = LocalDateTime.now().minusSeconds(OFFLINE_THRESHOLD_SECONDS);
        for (ComputeNodeDO node : onlineNodes) {
            if (ComputeNodeServiceImpl.isPlatformNode(node)) {
                continue;
            }
            String heartbeat = stringRedisTemplate.opsForValue().get(HEARTBEAT_KEY_PREFIX + node.getId());
            boolean redisAlive = heartbeat != null;
            boolean dbAlive = node.getLastHeartbeatAt() != null && node.getLastHeartbeatAt().isAfter(threshold);
            if (!redisAlive && !dbAlive) {
                node.setStatus(NodeStatusEnum.OFFLINE.getStatus());
                computeNodeMapper.updateById(node);
                log.warn("节点离线: id={}, host={}", node.getId(), node.getHost());
            }
        }
    }

}
