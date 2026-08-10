package com.basiclab.iot.video.kafka;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.media.DvrUploadService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.consumer.OffsetAndMetadata;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.SmartLifecycle;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

/**
 * Consumes {@code media.dvr.completed} and calls {@link DvrUploadService#processDvrEvent},
 * aligned with Python {@code services/media_upload_worker/run_worker.py} retry/DLQ semantics.
 * <p>
 * Gated: only starts when {@code video.media.upload-mode} is {@code kafka} or {@code hybrid};
 * default {@code sync} (mini/local) does not require a broker.
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class DvrUploadKafkaConsumerRunner implements SmartLifecycle {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {};

    private final VideoProperties videoProperties;
    private final DvrUploadService dvrUploadService;

    private volatile boolean running;
    private volatile boolean started;
    private Thread consumerThread;

    @Override
    public void start() {
        if (started) {
            return;
        }
        started = true;
        if (!shouldConsume()) {
            log.info(
                    "DVR Kafka consumer not started: upload-mode={} (sync=broker not required)",
                    videoProperties.getMedia().getUploadMode()
            );
            return;
        }
        running = true;
        consumerThread = new Thread(this::consumeLoop, "media-upload-worker-dvr");
        consumerThread.setDaemon(true);
        consumerThread.start();
    }

    @Override
    public void stop() {
        running = false;
        if (consumerThread != null) {
            consumerThread.interrupt();
            try {
                consumerThread.join(10_000L);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    @Override
    public boolean isRunning() {
        return running && consumerThread != null && consumerThread.isAlive();
    }

    @Override
    public int getPhase() {
        return Integer.MAX_VALUE;
    }

    private boolean shouldConsume() {
        String mode = normalizeUploadMode(videoProperties.getMedia().getUploadMode());
        return "kafka".equals(mode) || "hybrid".equals(mode);
    }

    private void consumeLoop() {
        VideoProperties.Media media = videoProperties.getMedia();
        log.info(
                "DVR Kafka consumer starting topic={} group={} bootstrap={}",
                media.getDvrCompletedTopic(),
                media.getDvrConsumerGroup(),
                resolveBootstrapServers()
        );

        while (running) {
            Properties props = consumerProperties(media);
            try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props)) {
                consumer.subscribe(Collections.singletonList(media.getDvrCompletedTopic()));
                log.info("DVR Kafka consumer subscribed topic={}", media.getDvrCompletedTopic());

                while (running) {
                    try {
                        ConsumerRecords<String, String> records = consumer.poll(
                                Duration.ofMillis(media.getDvrPollTimeoutMs())
                        );
                        for (ConsumerRecord<String, String> record : records) {
                            if (!running) {
                                break;
                            }
                            processRecord(consumer, record);
                        }
                    } catch (Exception e) {
                        if (running) {
                            log.error("DVR Kafka consumer poll error: {}", e.getMessage(), e);
                            sleepQuietly(5_000L);
                        }
                    }
                }
            } catch (Exception e) {
                if (running) {
                    log.error(
                            "DVR Kafka consumer broker unavailable — will retry in 5s: {}",
                            e.getMessage(),
                            e
                    );
                    sleepQuietly(5_000L);
                }
            }
        }
        log.info("DVR Kafka consumer stopped");
    }

    private Properties consumerProperties(VideoProperties.Media media) {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, resolveBootstrapServers());
        props.put(ConsumerConfig.GROUP_ID_CONFIG, media.getDvrConsumerGroup());
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "5");
        props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, "60000");
        props.put(ConsumerConfig.HEARTBEAT_INTERVAL_MS_CONFIG, "10000");
        props.put(ConsumerConfig.CLIENT_ID_CONFIG, "video-dvr-upload-consumer");
        return props;
    }

    private void processRecord(KafkaConsumer<String, String> consumer, ConsumerRecord<String, String> record) {
        Map<String, Object> event = parseEvent(record.value());
        if (event == null) {
            commitOffset(consumer, record);
            return;
        }
        Map<String, Object> mutableEvent = new HashMap<>(event);
        try {
            while (running) {
                boolean ok = dvrUploadService.processDvrEvent(mutableEvent);
                if (ok) {
                    commitOffset(consumer, record);
                    return;
                }
                int retries = intField(mutableEvent, "_retry") + 1;
                if (retries >= videoProperties.getMedia().getDvrMaxRetries()) {
                    dvrUploadService.publishDlq(mutableEvent, "max retries exceeded");
                    commitOffset(consumer, record);
                    return;
                }
                mutableEvent.put("_retry", retries);
                log.warn(
                        "DVR 处理失败，稍后重试 device={} retry={}",
                        mutableEvent.get("device_id"),
                        retries
                );
                sleepQuietly(Math.min(retries * 2L, 30L) * 1000L);
            }
        } catch (Exception e) {
            log.error("DVR 处理异常: {}", e.getMessage(), e);
            dvrUploadService.publishDlq(mutableEvent, e.getMessage());
            commitOffset(consumer, record);
        }
    }

    private static void commitOffset(KafkaConsumer<String, String> consumer, ConsumerRecord<String, String> record) {
        TopicPartition partition = new TopicPartition(record.topic(), record.partition());
        consumer.commitSync(Collections.singletonMap(partition, new OffsetAndMetadata(record.offset() + 1)));
    }

    private Map<String, Object> parseEvent(String payload) {
        if (payload == null || payload.isBlank()) {
            return Map.of();
        }
        try {
            return MAPPER.readValue(payload, MAP_TYPE);
        } catch (Exception e) {
            log.error("DVR Kafka message parse failed: {}", e.getMessage());
            return null;
        }
    }

    private String resolveBootstrapServers() {
        String servers = videoProperties.getKafka().getBootstrapServers();
        if (servers == null || servers.isBlank()) {
            return "localhost:9092";
        }
        if (servers.contains("Kafka") || servers.contains("kafka-server")) {
            return "localhost:9092";
        }
        return servers;
    }

    private static String normalizeUploadMode(String mode) {
        if (mode == null) {
            return "sync";
        }
        return mode.trim().toLowerCase();
    }

    private static int intField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return 0;
        }
        try {
            return Integer.parseInt(String.valueOf(data.get(key)));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private static void sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
