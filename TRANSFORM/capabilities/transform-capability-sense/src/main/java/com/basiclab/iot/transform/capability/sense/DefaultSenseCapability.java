package com.basiclab.iot.transform.capability.sense;

import com.basiclab.iot.transform.core.sense.NodeSenseSnapshot;
import lombok.extern.slf4j.Slf4j;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.util.UUID;

/**
 * 默认自感知实现：无状态，仅读本机 JVM/OS 指标。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class DefaultSenseCapability implements SenseCapability {

    private final String instanceId;

    public DefaultSenseCapability() {
        this.instanceId = UUID.randomUUID().toString().replace("-", "");
    }

    public DefaultSenseCapability(String instanceId) {
        this.instanceId = instanceId;
    }

    public String getInstanceId() {
        return instanceId;
    }

    @Override
    public NodeSenseSnapshot sense() {
        MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
        long used = memory.getHeapMemoryUsage().getUsed() / (1024 * 1024);
        long max = memory.getHeapMemoryUsage().getMax() / (1024 * 1024);
        double cpu = ManagementFactory.getOperatingSystemMXBean().getSystemLoadAverage();
        return NodeSenseSnapshot.builder()
                .instanceId(instanceId)
                .cpuLoad(cpu)
                .heapUsedMb(used)
                .heapMaxMb(max)
                .timestampEpochMs(System.currentTimeMillis())
                .build();
    }

    @Override
    public String adapt(NodeSenseSnapshot snapshot) {
        if (snapshot.getMaxConsumerLag() > 100_000) {
            log.warn("[adapt] lag high, hint scale-out: lag={}", snapshot.getMaxConsumerLag());
            return "SCALE_HINT";
        }
        if (snapshot.getDeliverSuccessRate() < 0.9 && snapshot.getDeliverSuccessRate() > 0) {
            return "DEGRADE_PARTY";
        }
        return "KEEP";
    }
}
