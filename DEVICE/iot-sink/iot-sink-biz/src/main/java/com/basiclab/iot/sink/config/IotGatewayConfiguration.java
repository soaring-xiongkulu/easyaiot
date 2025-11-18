package com.basiclab.iot.sink.config;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.protocol.emqx.IotEmqxAuthEventProtocol;
import com.basiclab.iot.sink.protocol.emqx.IotEmqxDownstreamSubscriber;
import com.basiclab.iot.sink.protocol.emqx.IotEmqxUpstreamProtocol;
import com.basiclab.iot.sink.protocol.http.IotHttpDownstreamSubscriber;
import com.basiclab.iot.sink.protocol.http.IotHttpUpstreamProtocol;
import com.basiclab.iot.sink.protocol.mqtt.IotMqttDownstreamSubscriber;
import com.basiclab.iot.sink.protocol.mqtt.IotMqttUpstreamProtocol;
import com.basiclab.iot.sink.protocol.mqtt.manager.IotMqttConnectionManager;
import com.basiclab.iot.sink.protocol.mqtt.router.IotMqttDownstreamHandler;
import com.basiclab.iot.sink.protocol.tcp.IotTcpDownstreamSubscriber;
import com.basiclab.iot.sink.protocol.tcp.IotTcpUpstreamProtocol;
import com.basiclab.iot.sink.protocol.tcp.manager.IotTcpConnectionManager;
import com.basiclab.iot.sink.messagebus.publisher.IotDeviceService;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import io.vertx.core.Vertx;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(IotGatewayProperties.class)
@Slf4j
public class IotGatewayConfiguration {

    /**
 * IotGatewayConfiguration
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Configuration
    @ConditionalOnProperty(prefix = "basiclab.iot.sink.protocol.http", name = "enabled", havingValue = "true")
    @Slf4j
    public static class HttpProtocolConfiguration {

        @Bean
        public IotHttpUpstreamProtocol iotHttpUpstreamProtocol(IotGatewayProperties gatewayProperties) {
            return new IotHttpUpstreamProtocol(gatewayProperties.getProtocol().getHttp());
        }

        @Bean
        public IotHttpDownstreamSubscriber iotHttpDownstreamSubscriber(IotHttpUpstreamProtocol httpUpstreamProtocol,
                IotMessageBus messageBus) {
            return new IotHttpDownstreamSubscriber(httpUpstreamProtocol, messageBus);
        }
    }

    /**
     * IoT 网关 EMQX 协议配置类
     */
    @Configuration
    @ConditionalOnProperty(prefix = "basiclab.iot.sink.protocol.emqx", name = "enabled", havingValue = "true")
    @Slf4j
    public static class EmqxProtocolConfiguration {

        @Bean(destroyMethod = "close")
        public Vertx emqxVertx() {
            return Vertx.vertx();
        }

        @Bean
        public IotEmqxAuthEventProtocol iotEmqxAuthEventProtocol(IotGatewayProperties gatewayProperties,
                Vertx emqxVertx) {
            return new IotEmqxAuthEventProtocol(gatewayProperties.getProtocol().getEmqx(), emqxVertx);
        }

        @Bean
        public IotEmqxUpstreamProtocol iotEmqxUpstreamProtocol(IotGatewayProperties gatewayProperties,
                Vertx emqxVertx) {
            return new IotEmqxUpstreamProtocol(gatewayProperties.getProtocol().getEmqx(), emqxVertx);
        }

        @Bean
        public IotEmqxDownstreamSubscriber iotEmqxDownstreamSubscriber(IotEmqxUpstreamProtocol mqttUpstreamProtocol,
                IotMessageBus messageBus) {
            return new IotEmqxDownstreamSubscriber(mqttUpstreamProtocol, messageBus);
        }
    }

    /**
     * IoT 网关 TCP 协议配置类
     */
    @Configuration
    @ConditionalOnProperty(prefix = "basiclab.iot.sink.protocol.tcp", name = "enabled", havingValue = "true")
    @Slf4j
    public static class TcpProtocolConfiguration {

        @Bean(destroyMethod = "close")
        public Vertx tcpVertx() {
            return Vertx.vertx();
        }

        @Bean
        public IotTcpUpstreamProtocol iotTcpUpstreamProtocol(IotGatewayProperties gatewayProperties,
                                                             IotDeviceService deviceService,
                                                             IotDeviceMessageService messageService,
                                                             IotTcpConnectionManager connectionManager,
                                                             Vertx tcpVertx) {
            return new IotTcpUpstreamProtocol(gatewayProperties.getProtocol().getTcp(),
                    deviceService, messageService, connectionManager, tcpVertx);
        }

        @Bean
        public IotTcpDownstreamSubscriber iotTcpDownstreamSubscriber(IotTcpUpstreamProtocol protocolHandler,
                                                                     IotDeviceMessageService messageService,
                                                                     IotDeviceService deviceService,
                                                                     IotTcpConnectionManager connectionManager,
                                                                     IotMessageBus messageBus) {
            return new IotTcpDownstreamSubscriber(protocolHandler, messageService, deviceService, connectionManager,
                    messageBus);
        }

    }

    /**
     * IoT 网关 MQTT 协议配置类
     */
    @Configuration
    @ConditionalOnProperty(prefix = "basiclab.iot.sink.protocol.mqtt", name = "enabled", havingValue = "true")
    @Slf4j
    public static class MqttProtocolConfiguration {

        @Bean(destroyMethod = "close")
        public Vertx mqttVertx() {
            return Vertx.vertx();
        }

        @Bean
        public IotMqttUpstreamProtocol iotMqttUpstreamProtocol(IotGatewayProperties gatewayProperties,
                                                               IotDeviceMessageService messageService,
                                                               IotMqttConnectionManager connectionManager,
                                                               Vertx mqttVertx) {
            return new IotMqttUpstreamProtocol(gatewayProperties.getProtocol().getMqtt(), messageService,
                    connectionManager, mqttVertx);
        }

        @Bean
        public IotMqttDownstreamHandler iotMqttDownstreamHandler(IotDeviceMessageService messageService,
                                                                 IotMqttConnectionManager connectionManager) {
            return new IotMqttDownstreamHandler(messageService, connectionManager);
        }

        @Bean
        public IotMqttDownstreamSubscriber iotMqttDownstreamSubscriber(IotMqttUpstreamProtocol mqttUpstreamProtocol,
                                                                       IotMqttDownstreamHandler downstreamHandler,
                                                                       IotMessageBus messageBus) {
            return new IotMqttDownstreamSubscriber(mqttUpstreamProtocol, downstreamHandler, messageBus);
        }

    }

}
