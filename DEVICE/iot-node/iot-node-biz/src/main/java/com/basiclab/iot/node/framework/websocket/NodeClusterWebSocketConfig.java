package com.basiclab.iot.node.framework.websocket;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

import javax.annotation.Resource;

@Configuration
@EnableWebSocket
public class NodeClusterWebSocketConfig implements WebSocketConfigurer {

    @Resource
    private NodeClusterWebSocketHandler nodeClusterWebSocketHandler;

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(nodeClusterWebSocketHandler, "/node/ws/cluster-metrics")
                .setAllowedOriginPatterns("*");
    }

}
