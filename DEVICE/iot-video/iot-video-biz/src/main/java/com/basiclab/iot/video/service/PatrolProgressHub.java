package com.basiclab.iot.video.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

/**
 * 巡检进度 SSE 订阅中心，对齐 Python {@code patrol_progress_hub}。
 */
@Slf4j
@Component
public class PatrolProgressHub {

    private static final int QUEUE_CAPACITY = 64;
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final Map<Long, List<BlockingQueue<Map<String, Object>>>> subscribers = new ConcurrentHashMap<>();

    public SseEmitter subscribe(long sessionId, Map<String, Object> initialPayload) {
        SseEmitter emitter = new SseEmitter(0L);
        BlockingQueue<Map<String, Object>> queue = new LinkedBlockingQueue<>(QUEUE_CAPACITY);
        subscribers.computeIfAbsent(sessionId, ignored -> new ArrayList<>()).add(queue);

        Thread worker = new Thread(() -> streamLoop(sessionId, emitter, queue, initialPayload), "patrol-sse-" + sessionId);
        worker.setDaemon(true);
        worker.start();

        emitter.onCompletion(() -> unsubscribe(sessionId, queue));
        emitter.onTimeout(() -> unsubscribe(sessionId, queue));
        emitter.onError(ex -> unsubscribe(sessionId, queue));
        return emitter;
    }

    public void publish(long sessionId, String eventType, Map<String, Object> data) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("type", eventType);
        payload.put("data", data);
        List<BlockingQueue<Map<String, Object>>> subs = subscribers.get(sessionId);
        if (subs == null || subs.isEmpty()) {
            return;
        }
        for (BlockingQueue<Map<String, Object>> queue : List.copyOf(subs)) {
            if (!queue.offer(payload)) {
                queue.poll();
                queue.offer(payload);
            }
        }
    }

    private void streamLoop(
            long sessionId,
            SseEmitter emitter,
            BlockingQueue<Map<String, Object>> queue,
            Map<String, Object> initialPayload
    ) {
        try {
            sendEvent(emitter, "progress", initialPayload);
            while (true) {
                try {
                    Map<String, Object> msg = queue.poll(25, TimeUnit.SECONDS);
                    if (msg == null) {
                        emitter.send(SseEmitter.event().comment("keepalive"));
                        continue;
                    }
                    String eventType = String.valueOf(msg.getOrDefault("type", "progress"));
                    @SuppressWarnings("unchecked")
                    Map<String, Object> data = (Map<String, Object>) msg.get("data");
                    sendEvent(emitter, eventType, data != null ? data : Map.of());
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        } catch (IOException e) {
            log.debug("patrol SSE closed sessionId={}: {}", sessionId, e.getMessage());
        } finally {
            unsubscribe(sessionId, queue);
            emitter.complete();
        }
    }

    private void sendEvent(SseEmitter emitter, String eventType, Map<String, Object> data) throws IOException {
        emitter.send(SseEmitter.event()
                .name(eventType)
                .data(MAPPER.writeValueAsString(data)));
    }

    private void unsubscribe(long sessionId, BlockingQueue<Map<String, Object>> queue) {
        List<BlockingQueue<Map<String, Object>>> subs = subscribers.get(sessionId);
        if (subs == null) {
            return;
        }
        subs.remove(queue);
        if (subs.isEmpty()) {
            subscribers.remove(sessionId);
        }
    }
}
