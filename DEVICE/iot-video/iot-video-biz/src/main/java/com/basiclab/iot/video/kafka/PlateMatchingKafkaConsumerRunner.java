package com.basiclab.iot.video.kafka;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.service.PlateMatchingService;
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
import java.util.Map;
import java.util.Properties;

/**
 * Consumes {@code iot-plate-matching} and calls {@link PlateMatchingService#process},
 * mirroring Python worker / iot-sink {@code PlateMatchingConsumer} → VIDEO process path.
 * <p>
 * Gated: only starts when {@code use-direct-process=false} and
 * {@code plate-matching-consumer-enabled=true}.
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "video", name = "skip-background-tasks", havingValue = "false", matchIfMissing = true)
public class PlateMatchingKafkaConsumerRunner implements SmartLifecycle {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {};

    private final VideoProperties videoProperties;
    private final PlateMatchingService plateMatchingService;

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
                    "Plate matching Kafka consumer not started: use-direct-process={} consumer-enabled={}",
                    videoProperties.getMatching().isUseDirectProcess(),
                    videoProperties.getMatching().isPlateMatchingConsumerEnabled()
            );
            return;
        }
        running = true;
        consumerThread = new Thread(this::consumeLoop, "video-plate-matching-consumer");
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
        VideoProperties.Matching matching = videoProperties.getMatching();
        return !matching.isUseDirectProcess() && matching.isPlateMatchingConsumerEnabled();
    }

    private void consumeLoop() {
        VideoProperties.Matching matching = videoProperties.getMatching();
        String topic = matching.getPlateMatchingTopic();
        String group = matching.getPlateMatchingConsumerGroup();
        log.info(
                "Plate matching Kafka consumer starting topic={} group={} bootstrap={}",
                topic,
                group,
                resolveBootstrapServers()
        );

        while (running) {
            Properties props = consumerProperties(matching);
            try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props)) {
                consumer.subscribe(Collections.singletonList(topic));
                log.info("Plate matching Kafka consumer subscribed topic={}", topic);

                while (running) {
                    try {
                        ConsumerRecords<String, String> records = consumer.poll(
                                Duration.ofMillis(matching.getPlateMatchingPollTimeoutMs())
                        );
                        for (ConsumerRecord<String, String> record : records) {
                            if (!running) {
                                break;
                            }
                            processRecord(consumer, record);
                        }
                    } catch (Exception e) {
                        if (running) {
                            log.error("Plate matching Kafka consumer poll error: {}", e.getMessage(), e);
                            sleepQuietly(5_000L);
                        }
                    }
                }
            } catch (Exception e) {
                if (running) {
                    log.error(
                            "Plate matching Kafka consumer broker unavailable — will retry in 5s: {}",
                            e.getMessage(),
                            e
                    );
                    sleepQuietly(5_000L);
                }
            }
        }
        log.info("Plate matching Kafka consumer stopped");
    }

    private Properties consumerProperties(VideoProperties.Matching matching) {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, resolveBootstrapServers());
        props.put(ConsumerConfig.GROUP_ID_CONFIG, matching.getPlateMatchingConsumerGroup());
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "10");
        props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, "60000");
        props.put(ConsumerConfig.HEARTBEAT_INTERVAL_MS_CONFIG, "10000");
        props.put(ConsumerConfig.CLIENT_ID_CONFIG, "video-plate-matching-consumer");
        return props;
    }

    private void processRecord(KafkaConsumer<String, String> consumer, ConsumerRecord<String, String> record) {
        Map<String, Object> payload = parsePayload(record.value());
        if (payload == null) {
            commitOffset(consumer, record);
            return;
        }
        try {
            Map<String, Object> result = plateMatchingService.process(payload);
            log.info(
                    "Plate matching Kafka consumed: topic={} partition={} offset={} matched={} alert_id={}",
                    record.topic(),
                    record.partition(),
                    record.offset(),
                    result.get("matched"),
                    result.get("alert_id")
            );
            commitOffset(consumer, record);
        } catch (Exception e) {
            log.error(
                    "Plate matching Kafka process failed: topic={} offset={} error={}",
                    record.topic(),
                    record.offset(),
                    e.getMessage(),
                    e
            );
            // Do not ACK — allow Kafka retry (aligned with iot-sink PlateMatchingConsumer).
        }
    }

    private static void commitOffset(KafkaConsumer<String, String> consumer, ConsumerRecord<String, String> record) {
        TopicPartition partition = new TopicPartition(record.topic(), record.partition());
        consumer.commitSync(Collections.singletonMap(partition, new OffsetAndMetadata(record.offset() + 1)));
    }

    private Map<String, Object> parsePayload(String payload) {
        if (payload == null || payload.isBlank()) {
            return Map.of();
        }
        try {
            return MAPPER.readValue(payload, MAP_TYPE);
        } catch (Exception e) {
            log.error("Plate matching Kafka message parse failed: {}", e.getMessage());
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

    private static void sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
