package com.basiclab.iot.transform.runtime.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * TRANSFORM 运行时配置：启用哪些渠道即加入哪些约定 Group。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ConfigurationProperties(prefix = "transform")
public class TransformRuntimeProperties {

    /** 可选：固定实例 ID；为空则随机生成（无状态场景推荐随机） */
    private String instanceId;

    /** 可选：所在 iot-node 节点 ID，便于泳道观测 */
    private String nodeId;

    /**
     * 机器维度主机标识（建议填计算节点 IP / 主机名）。
     * Docker 内默认 hostname 是容器短 ID，不设此值会导致集群页按容器拆成多台「假机器」。
     */
    private String host = "";

    /** full、consume、deliver、edge、backup。edge 不订阅 iot-sink。 */
    private String role = "full";

    private String backupDir = "./data/transform-backup";

    private Http http = new Http();

    private Channels channels = new Channels();

    private Sense sense = new Sense();
    private Outbox outbox = new Outbox();

    @Data
    public static class Channels {
        /** 主输入：iot-sink Kafka */
        private boolean kafka = true;
        private boolean http = true;
        private boolean mqtt = false;
        private boolean jdbc = false;
        private boolean party = true;
    }

    @Data
    public static class Sense {
        /** 自感知周期（毫秒） */
        private long intervalMs = 15000L;
    }

    @Data
    public static class Http {
        private long timeoutMs = 10000L;
    }

    @Data
    public static class Outbox {
        private int batchSize = 100;
        private int maxAttempts = 10;
        /** Outbox 中继轮询间隔（毫秒） */
        private long pollIntervalMs = 1000L;
    }
}
