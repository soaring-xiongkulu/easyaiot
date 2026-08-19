package com.basiclab.iot.node.framework.websocket;

import com.basiclab.iot.node.service.NodeClusterMetricsBroadcaster;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import javax.annotation.Resource;
import java.io.IOException;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class NodeClusterWebSocketHandler extends TextWebSocketHandler {

    private final Set<WebSocketSession> sessions = ConcurrentHashMap.newKeySet();

    @Resource
    private NodeClusterMetricsBroadcaster nodeClusterMetricsBroadcaster;

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        log.debug("集群指标 WebSocket 已连接: {}", session.getId());
        nodeClusterMetricsBroadcaster.sendSnapshot(session);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        log.debug("集群指标 WebSocket 已断开: {}", session.getId());
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        sessions.remove(session);
        log.warn("集群指标 WebSocket 传输异常: {}", session.getId(), exception);
        closeQuietly(session);
    }

    public void broadcast(String payload) {
        TextMessage message = new TextMessage(payload);
        for (WebSocketSession session : sessions) {
            if (!session.isOpen()) {
                sessions.remove(session);
                continue;
            }
            try {
                session.sendMessage(message);
            } catch (IOException ex) {
                log.warn("推送集群指标失败: {}", session.getId(), ex);
                sessions.remove(session);
                closeQuietly(session);
            }
        }
    }

    private void closeQuietly(WebSocketSession session) {
        try {
            session.close();
        } catch (IOException ignored) {
            // ignore
        }
    }

}
