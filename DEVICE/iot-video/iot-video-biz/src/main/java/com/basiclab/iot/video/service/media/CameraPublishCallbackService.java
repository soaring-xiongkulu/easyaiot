package com.basiclab.iot.video.service.media;

import com.basiclab.iot.video.config.VideoProperties;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * SRS on_publish callback — fast ack + async stream conflict resolution (mirrors Python camera.on_publish_callback).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CameraPublishCallbackService {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final ExecutorService EXECUTOR = Executors.newCachedThreadPool(r -> {
        Thread thread = new Thread(r, "srs-on-publish");
        thread.setDaemon(true);
        return thread;
    });

    private final VideoProperties videoProperties;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(1))
            .build();

    public void handleOnPublish(Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            return;
        }
        String streamUrl = stringField(body, "stream_url");
        if (streamUrl.isEmpty()) {
            return;
        }
        String clientId = stringField(body, "client_id");
        EXECUTOR.submit(() -> checkAndStopExistingStreamAsync(streamUrl, clientId));
    }

    private void checkAndStopExistingStreamAsync(String streamUrl, String clientId) {
        try {
            String streamPath = streamUrl.startsWith("/") ? streamUrl.substring(1) : streamUrl;
            String srsHost = videoProperties.getMedia().getSrsHost();
            String srsApiUrl = "http://" + srsHost + ":1985/api/v1/streams/";

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(srsApiUrl))
                    .timeout(Duration.ofSeconds(1))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                return;
            }

            JsonNode root = MAPPER.readTree(response.body());
            JsonNode streamList;
            if (root.has("streams")) {
                streamList = root.get("streams");
            } else if (root.isArray()) {
                streamList = root;
            } else {
                return;
            }

            for (JsonNode existingStream : streamList) {
                String streamApp = existingStream.path("app").asText("");
                String streamName = existingStream.path("stream").asText("");
                String fullStreamPath = streamName.isBlank() ? streamApp : streamApp + "/" + streamName;
                if (!matchesStream(streamPath, fullStreamPath)) {
                    continue;
                }
                JsonNode publish = existingStream.path("publish");
                String publishCid = publish.path("cid").asText("");
                if (!publishCid.isBlank() && !publishCid.equals(clientId)) {
                    log.warn("on_publish：检测到流 {} 已有发布者 (client_id={})，尝试停止...", streamPath, publishCid);
                    stopPublisher(srsHost, publishCid);
                }
                break;
            }
        } catch (Exception ex) {
            log.debug("on_publish 异步检查流冲突失败: {}", ex.getMessage());
        }
    }

    private void stopPublisher(String srsHost, String publishCid) {
        try {
            HttpRequest deleteRequest = HttpRequest.newBuilder()
                    .uri(URI.create("http://" + srsHost + ":1985/api/v1/clients/" + publishCid))
                    .timeout(Duration.ofSeconds(1))
                    .DELETE()
                    .build();
            HttpResponse<Void> stopResponse = httpClient.send(deleteRequest, HttpResponse.BodyHandlers.discarding());
            if (stopResponse.statusCode() == 200 || stopResponse.statusCode() == 204) {
                log.info("on_publish：已停止旧的发布者 {}", publishCid);
            } else {
                log.warn("on_publish：停止旧发布者失败 status={}", stopResponse.statusCode());
            }
        } catch (Exception ex) {
            log.warn("on_publish：停止旧发布者异常: {}", ex.getMessage());
        }
    }

    private static boolean matchesStream(String streamPath, String fullStreamPath) {
        return streamPath.equals(fullStreamPath)
                || streamPath.endsWith(fullStreamPath)
                || fullStreamPath.endsWith(streamPath);
    }

    private static String stringField(Map<String, Object> data, String key) {
        if (data == null || data.get(key) == null) {
            return "";
        }
        return String.valueOf(data.get(key)).trim();
    }
}
