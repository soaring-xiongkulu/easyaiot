package com.basiclab.iot.sink.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.time.Duration;
import java.util.List;

@ConfigurationProperties(prefix = "basiclab.iot.sink")
@Validated
@Data
public class IotGatewayProperties {

    /**
     * 设备 RPC 服务配置
     */
    private RpcProperties rpc;
    /**
     * Token 配置
     */
    private TokenProperties token;

    /**
     * 协议配置
     */
    private ProtocolProperties protocol;

    /**
     * Topic 配置
     */
    private TopicProperties topic;

    @Data
    public static class RpcProperties {

        /**
         * 主程序 API 地址
         */
        @NotEmpty(message = "主程序 API 地址不能为空")
        private String url;
        /**
         * 连接超时时间
         */
        @NotNull(message = "连接超时时间不能为空")
        private Duration connectTimeout;
        /**
         * 读取超时时间
         */
        @NotNull(message = "读取超时时间不能为空")
        private Duration readTimeout;

    }

    @Data
    public static class TokenProperties {

        /**
         * 密钥
         */
        @NotEmpty(message = "密钥不能为空")
        private String secret;
        /**
         * 令牌有效期
         */
        @NotNull(message = "令牌有效期不能为空")
        private Duration expiration;

    }

    @Data
    public static class ProtocolProperties {

        /**
         * HTTP 组件配置
         */
        private HttpProperties http;

        /**
         * EMQX 组件配置
         */
        private EmqxProperties emqx;

        /**
         * TCP 组件配置
         */
        private TcpProperties tcp;

        /**
         * MQTT 组件配置
         */
        private MqttProperties mqtt;

    }

    @Data
    public static class HttpProperties {

        /**
         * 是否开启
         */
        @NotNull(message = "是否开启不能为空")
        private Boolean enabled = false;
        /**
         * 服务端口
         */
        private Integer serverPort;

        /**
         * 是否开启 SSL
         */
        @NotNull(message = "是否开启 SSL 不能为空")
        private Boolean sslEnabled = false;

        /**
         * SSL 证书路径
         */
        private String sslKeyPath;
        /**
         * SSL 证书路径
         */
        private String sslCertPath;

        /**
         * 是否开启鉴权（默认开启）
         */
        private Boolean authEnabled = true;

    }

    @Data
    public static class EmqxProperties {

        /**
         * 是否开启
         */
        @NotNull(message = "是否开启不能为空")
        private Boolean enabled = false;

        /**
         * HTTP 服务端口（默认：8090）
         */
        private Integer httpPort = 8090;

        /**
         * MQTT 服务器地址
         * 注意：仅在 enabled=true 时必填
         */
        private String mqttHost;

        /**
         * MQTT 服务器端口（默认：1883）
         */
        private Integer mqttPort = 1883;

        /**
         * MQTT 用户名
         * 注意：仅在 enabled=true 时必填
         */
        private String mqttUsername;

        /**
         * MQTT 密码
         * 注意：仅在 enabled=true 时必填
         */
        private String mqttPassword;

        /**
         * MQTT 客户端的 SSL 开关
         */
        private Boolean mqttSsl = false;

        /**
         * MQTT 客户端 ID（如果为空，系统将自动生成）
         * 注意：仅在 enabled=true 时必填
         */
        private String mqttClientId;

        /**
         * MQTT 订阅的主题
         * 注意：仅在 enabled=true 时必填
         */
        private List<String> mqttTopics;

        /**
         * 默认 QoS 级别
         * <p>
         * 0 - 最多一次
         * 1 - 至少一次
         * 2 - 刚好一次
         */
        private Integer mqttQos = 1;

        /**
         * 连接超时时间（秒）
         */
        private Integer connectTimeoutSeconds = 10;

        /**
         * 重连延迟时间（毫秒）
         */
        private Long reconnectDelayMs = 5000L;

        /**
         * 是否启用 Clean Session (清理会话)
         * true: 每次连接都是新会话，Broker 不保留离线消息和订阅关系。
         * 对于网关这类“永远在线”且会主动重新订阅的应用，建议为 true。
         */
        private Boolean cleanSession = true;

        /**
         * 心跳间隔（秒）
         * 用于保持连接活性，及时发现网络中断。
         */
        private Integer keepAliveIntervalSeconds = 60;

        /**
         * 最大未确认消息队列大小
         * 限制已发送但未收到 Broker 确认的 QoS 1/2 消息数量，用于流量控制。
         */
        private Integer maxInflightQueue = 10000;

        /**
         * 是否信任所有 SSL 证书
         * 警告：此配置会绕过证书验证，仅建议在开发和测试环境中使用！
         * 在生产环境中，应设置为 false，并配置正确的信任库。
         */
        private Boolean trustAll = false;

        /**
         * 遗嘱消息配置 (用于网关异常下线时通知其他系统)
         */
        private final Will will = new Will();

        /**
         * 高级 SSL/TLS 配置 (用于生产环境)
         */
        private final Ssl sslOptions = new Ssl();

        /**
         * 遗嘱消息 (Last Will and Testament)
         */
        @Data
        public static class Will {

            /**
             * 是否启用遗嘱消息
             */
            private boolean enabled = false;
            /**
             * 遗嘱消息主题
             */
            private String topic;
            /**
             * 遗嘱消息内容
             */
            private String payload;
            /**
             * 遗嘱消息 QoS 等级
             */
            private Integer qos = 1;
            /**
             * 遗嘱消息是否作为保留消息发布
             */
            private boolean retain = true;

        }

        /**
         * 高级 SSL/TLS 配置
         */
        @Data
        public static class Ssl {

            /**
             * 密钥库（KeyStore）路径，例如：classpath:certs/client.jks
             * 包含客户端自己的证书和私钥，用于向服务端证明身份（双向认证）。
             */
            private String keyStorePath;
            /**
             * 密钥库密码
             */
            private String keyStorePassword;
            /**
             * 信任库（TrustStore）路径，例如：classpath:certs/trust.jks
             * 包含服务端信任的 CA 证书，用于验证服务端的身份，防止中间人攻击。
             */
            private String trustStorePath;
            /**
             * 信任库密码
             */
            private String trustStorePassword;

        }

    }

    @Data
    public static class TcpProperties {

        /**
         * 是否开启
         */
        @NotNull(message = "是否开启不能为空")
        private Boolean enabled = false;

        /**
         * 服务器端口
         */
        private Integer port = 8091;

        /**
         * 心跳超时时间（毫秒）
         */
        private Long keepAliveTimeoutMs = 30000L;

        /**
         * 最大连接数
         */
        private Integer maxConnections = 1000;

        /**
         * 是否启用SSL
         */
        private Boolean sslEnabled = false;

        /**
         * SSL证书路径
         */
        private String sslCertPath;

        /**
         * SSL私钥路径
         */
        private String sslKeyPath;

    }

    @Data
    public static class MqttProperties {

        /**
         * 是否开启
         */
        @NotNull(message = "是否开启不能为空")
        private Boolean enabled = false;

        /**
         * 服务器端口
         */
        private Integer port = 1883;

        /**
         * 最大消息大小（字节）
         */
        private Integer maxMessageSize = 8192;

        /**
         * 连接超时时间（秒）
         */
        private Integer connectTimeoutSeconds = 60;
        /**
         * 保持连接超时时间（秒）
         */
        private Integer keepAliveTimeoutSeconds = 300;

        /**
         * 是否启用 SSL
         */
        private Boolean sslEnabled = false;
        /**
         * SSL 配置
         */
        private SslOptions sslOptions = new SslOptions();

        /**
         * SSL 配置选项
         */
        @Data
        public static class SslOptions {

            /**
             * 密钥证书选项
             */
            private io.vertx.core.net.KeyCertOptions keyCertOptions;
            /**
             * 信任选项
             */
            private io.vertx.core.net.TrustOptions trustOptions;
            /**
             * SSL 证书路径
             */
            private String certPath;
            /**
             * SSL 私钥路径
             */
            private String keyPath;
            /**
             * 信任存储路径
             */
            private String trustStorePath;
            /**
             * 信任存储密码
             */
            private String trustStorePassword;

        }

    }

    @Data
    public static class TopicProperties {

        /**
         * 配置管理相关 Topic 开关
         */
        private ConfigTopicProperties config = new ConfigTopicProperties();

        /**
         * 设备标签管理相关 Topic 开关
         */
        private DeviceTagTopicProperties deviceTag = new DeviceTagTopicProperties();

        /**
         * 设备影子相关 Topic 开关
         */
        private ShadowTopicProperties shadow = new ShadowTopicProperties();

        /**
         * 时钟同步相关 Topic 开关
         */
        private NtpTopicProperties ntp = new NtpTopicProperties();

        /**
         * 广播消息相关 Topic 开关
         */
        private BroadcastTopicProperties broadcast = new BroadcastTopicProperties();

        /**
         * OTA 固件升级相关 Topic 开关
         */
        private OtaTopicProperties ota = new OtaTopicProperties();

        /**
         * 服务调用相关 Topic 开关
         */
        private ServiceTopicProperties service = new ServiceTopicProperties();

        /**
         * 属性相关 Topic 开关
         */
        private PropertyTopicProperties property = new PropertyTopicProperties();

        /**
         * 事件相关 Topic 开关
         */
        private EventTopicProperties event = new EventTopicProperties();

        /**
         * 配置管理相关 Topic 开关
         */
        @Data
        public static class ConfigTopicProperties {
            /**
             * 云端下行推送配置（设备订阅）
             */
            private Boolean downstreamPush = true;
            /**
             * 云端下行回复配置查询（设备订阅）
             */
            private Boolean downstreamQueryAck = true;
            /**
             * 设备上行查询配置（设备发布）
             */
            private Boolean upstreamQuery = true;
        }

        /**
         * 设备标签管理相关 Topic 开关
         */
        @Data
        public static class DeviceTagTopicProperties {
            /**
             * 云端下行回复标签上报（设备订阅）
             */
            private Boolean downstreamReportAck = true;
            /**
             * 设备上行删除标签（设备发布）
             */
            private Boolean upstreamDelete = true;
            /**
             * 设备上行上报标签（设备发布）
             */
            private Boolean upstreamReport = true;
            /**
             * 云端下行回复标签删除（设备订阅）
             */
            private Boolean downstreamDeleteAck = true;
        }

        /**
         * 设备影子相关 Topic 开关
         */
        @Data
        public static class ShadowTopicProperties {
            /**
             * 云端下行推送影子期望值（设备订阅）
             */
            private Boolean downstreamDesired = true;
            /**
             * 设备上行上报影子状态（设备发布）
             */
            private Boolean upstreamReport = true;
        }

        /**
         * 时钟同步相关 Topic 开关
         */
        @Data
        public static class NtpTopicProperties {
            /**
             * 云端下行回复 NTP 同步请求（设备订阅）
             */
            private Boolean downstreamResponse = true;
            /**
             * 设备上行请求 NTP 同步（设备发布）
             */
            private Boolean upstreamRequest = true;
        }

        /**
         * 广播消息相关 Topic 开关
         */
        @Data
        public static class BroadcastTopicProperties {
            /**
             * 云端下行广播消息（设备订阅）
             */
            private Boolean downstream = true;
        }

        /**
         * OTA 固件升级相关 Topic 开关
         */
        @Data
        public static class OtaTopicProperties {
            /**
             * 云端下行推送固件升级任务（设备订阅）
             */
            private Boolean downstreamUpgradeTask = true;
            /**
             * 设备上行上报固件版本信息（设备发布）
             */
            private Boolean upstreamVersionReport = true;
            /**
             * 设备上行上报升级进度（设备发布）
             */
            private Boolean upstreamProgressReport = true;
            /**
             * 设备上行查询固件信息（设备发布）
             */
            private Boolean upstreamFirmwareQuery = true;
        }

        /**
         * 服务调用相关 Topic 开关
         */
        @Data
        public static class ServiceTopicProperties {
            /**
             * 云端下行调用设备服务（设备订阅）
             */
            private Boolean downstreamInvoke = true;
            /**
             * 设备上行响应服务调用（设备发布）
             */
            private Boolean upstreamInvokeResponse = true;
        }

        /**
         * 属性相关 Topic 开关
         */
        @Data
        public static class PropertyTopicProperties {
            /**
             * 云端下行设置属性期望值（设备订阅）
             */
            private Boolean downstreamDesiredSet = true;
            /**
             * 设备上行回复属性期望值设置（设备发布）
             */
            private Boolean upstreamDesiredSetAck = true;
            /**
             * 云端下行查询属性期望值（设备订阅）
             */
            private Boolean downstreamDesiredQuery = true;
            /**
             * 设备上行回复属性期望值查询（设备发布）
             */
            private Boolean upstreamDesiredQueryResponse = true;
            /**
             * 云端下行回复属性上报（设备订阅）
             */
            private Boolean downstreamReportAck = true;
            /**
             * 设备上行上报属性（设备发布）
             */
            private Boolean upstreamReport = true;
        }

        /**
         * 事件相关 Topic 开关
         */
        @Data
        public static class EventTopicProperties {
            /**
             * 云端下行回复事件上报（设备订阅）
             */
            private Boolean downstreamReportAck = true;
            /**
             * 设备上行上报事件（设备发布）
             */
            private Boolean upstreamReport = true;
        }

        /**
         * 根据 Topic 枚举获取是否启用
         *
         * @param topicEnum Topic 枚举
         * @return 是否启用
         */
        public boolean isEnabled(com.basiclab.iot.sink.enums.IotDeviceTopicEnum topicEnum) {
            if (topicEnum == null) {
                return false;
            }
            switch (topicEnum) {
                // 配置管理
                case CONFIG_DOWNSTREAM_PUSH:
                    return config.getDownstreamPush();
                case CONFIG_DOWNSTREAM_QUERY_ACK:
                    return config.getDownstreamQueryAck();
                case CONFIG_UPSTREAM_QUERY:
                    return config.getUpstreamQuery();
                // 设备标签管理
                case DEVICE_TAG_DOWNSTREAM_REPORT_ACK:
                    return deviceTag.getDownstreamReportAck();
                case DEVICE_TAG_UPSTREAM_DELETE:
                    return deviceTag.getUpstreamDelete();
                case DEVICE_TAG_UPSTREAM_REPORT:
                    return deviceTag.getUpstreamReport();
                case DEVICE_TAG_DOWNSTREAM_DELETE_ACK:
                    return deviceTag.getDownstreamDeleteAck();
                // 设备影子
                case SHADOW_DOWNSTREAM_DESIRED:
                    return shadow.getDownstreamDesired();
                case SHADOW_UPSTREAM_REPORT:
                    return shadow.getUpstreamReport();
                // 时钟同步
                case NTP_DOWNSTREAM_RESPONSE:
                    return ntp.getDownstreamResponse();
                case NTP_UPSTREAM_REQUEST:
                    return ntp.getUpstreamRequest();
                // 广播消息
                case BROADCAST_DOWNSTREAM:
                    return broadcast.getDownstream();
                // OTA 固件升级
                case OTA_DOWNSTREAM_UPGRADE_TASK:
                    return ota.getDownstreamUpgradeTask();
                case OTA_UPSTREAM_VERSION_REPORT:
                    return ota.getUpstreamVersionReport();
                case OTA_UPSTREAM_PROGRESS_REPORT:
                    return ota.getUpstreamProgressReport();
                case OTA_UPSTREAM_FIRMWARE_QUERY:
                    return ota.getUpstreamFirmwareQuery();
                // 服务调用
                case SERVICE_DOWNSTREAM_INVOKE:
                    return service.getDownstreamInvoke();
                case SERVICE_UPSTREAM_INVOKE_RESPONSE:
                    return service.getUpstreamInvokeResponse();
                // 属性期望值设置
                case PROPERTY_DOWNSTREAM_DESIRED_SET:
                    return property.getDownstreamDesiredSet();
                case PROPERTY_UPSTREAM_DESIRED_SET_ACK:
                    return property.getUpstreamDesiredSetAck();
                // 属性期望值获取
                case PROPERTY_DOWNSTREAM_DESIRED_QUERY:
                    return property.getDownstreamDesiredQuery();
                case PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE:
                    return property.getUpstreamDesiredQueryResponse();
                // 属性上报
                case PROPERTY_DOWNSTREAM_REPORT_ACK:
                    return property.getDownstreamReportAck();
                case PROPERTY_UPSTREAM_REPORT:
                    return property.getUpstreamReport();
                // 事件上报
                case EVENT_DOWNSTREAM_REPORT_ACK:
                    return event.getDownstreamReportAck();
                case EVENT_UPSTREAM_REPORT:
                    return event.getUpstreamReport();
                default:
                    return true; // 默认启用，兼容新增的 topic
            }
        }
    }

}
