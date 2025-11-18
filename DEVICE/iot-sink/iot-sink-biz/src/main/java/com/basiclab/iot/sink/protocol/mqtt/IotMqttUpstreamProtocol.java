package com.basiclab.iot.sink.protocol.mqtt;

import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.protocol.mqtt.manager.IotMqttConnectionManager;
import com.basiclab.iot.sink.protocol.mqtt.router.IotMqttUpstreamHandler;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import io.vertx.core.Vertx;
import io.vertx.mqtt.MqttServer;
import io.vertx.mqtt.MqttServerOptions;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 * IotMqttUpstreamProtocol
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
public class IotMqttUpstreamProtocol {

    private final IotGatewayProperties.MqttProperties mqttProperties;

    private final IotDeviceMessageService messageService;

    private final IotMqttConnectionManager connectionManager;

    private final Vertx vertx;

    @Getter
    private final String serverId;

    private MqttServer mqttServer;

    public IotMqttUpstreamProtocol(IotGatewayProperties.MqttProperties mqttProperties,
                                   IotDeviceMessageService messageService,
                                   IotMqttConnectionManager connectionManager,
                                   Vertx vertx) {
        this.mqttProperties = mqttProperties;
        this.messageService = messageService;
        this.connectionManager = connectionManager;
        this.vertx = vertx;
        this.serverId = IotDeviceMessageUtils.generateServerId(mqttProperties.getPort());
    }

    // TODO @haohao：这里的编写，是不是和 tcp 对应的，风格保持一致哈；
    @PostConstruct
    public void start() {
        // 创建服务器选项
        MqttServerOptions options = new MqttServerOptions()
                .setPort(mqttProperties.getPort())
                .setMaxMessageSize(mqttProperties.getMaxMessageSize())
                .setTimeoutOnConnect(mqttProperties.getConnectTimeoutSeconds());

        // 配置 SSL（如果启用）
        if (Boolean.TRUE.equals(mqttProperties.getSslEnabled())) {
            options.setSsl(true)
                    .setKeyCertOptions(mqttProperties.getSslOptions().getKeyCertOptions())
                    .setTrustOptions(mqttProperties.getSslOptions().getTrustOptions());
        }

        // 创建服务器并设置连接处理器
        mqttServer = MqttServer.create(vertx, options);
        mqttServer.endpointHandler(endpoint -> {
            IotMqttUpstreamHandler handler = new IotMqttUpstreamHandler(this, messageService, connectionManager);
            handler.handle(endpoint);
        });

        // 启动服务器
        try {
            mqttServer.listen().result();
            log.info("[start][IoT 网关 MQTT 协议启动成功，端口：{}]", mqttProperties.getPort());
        } catch (Exception e) {
            log.error("[start][IoT 网关 MQTT 协议启动失败]", e);
            throw e;
        }
    }

    @PreDestroy
    public void stop() {
        if (mqttServer != null) {
            try {
                mqttServer.close().result();
                log.info("[stop][IoT 网关 MQTT 协议已停止]");
            } catch (Exception e) {
                log.error("[stop][IoT 网关 MQTT 协议停止失败]", e);
            }
        }
    }
}
