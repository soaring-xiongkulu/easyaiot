package com.basiclab.iot.transform.channel.http;

import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.group.GroupNames;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HexFormat;

/**
 * HTTP/Webhook 投递渠道：加入 {@link GroupNames#HTTP_DELIVER} 横向扩展投递能力。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class HttpDeliverChannel implements TransformChannel {

    private volatile boolean joined;
    private final HttpClient client;
    private final ObjectMapper objectMapper;
    private final Duration timeout;

    public HttpDeliverChannel(HttpClient client, ObjectMapper objectMapper, Duration timeout) {
        this.client = client;
        this.objectMapper = objectMapper;
        this.timeout = timeout;
    }

    @Override
    public ChannelType type() {
        return ChannelType.HTTP;
    }

    @Override
    public String deliverGroup() {
        return GroupNames.HTTP_DELIVER;
    }

    @Override
    public void join() {
        joined = true;
        log.info("[HttpDeliverChannel] joined deliver group={}", deliverGroup());
    }

    @Override
    public void leave() {
        joined = false;
    }

    @Override
    public void deliver(TransformEnvelope envelope) {
        try {
            Object endpoint = envelope.getHeaders().get("endpoint");
            if (endpoint == null || endpoint.toString().isBlank()) {
                throw new IllegalArgumentException("http endpoint is required");
            }
            String body = objectMapper.writeValueAsString(envelope);
            HttpRequest.Builder request = HttpRequest.newBuilder(URI.create(endpoint.toString()))
                    .timeout(timeout)
                    .header("Content-Type", "application/json")
                    .header("X-Transform-Event-Id", envelope.getEventId())
                    .POST(HttpRequest.BodyPublishers.ofString(body));
            Object secret = envelope.getHeaders().get("partySecret");
            if (secret != null && !secret.toString().isBlank()) {
                request.header("X-Transform-Signature", hmac(body, secret.toString()));
            }
            HttpResponse<Void> response = client.send(request.build(), HttpResponse.BodyHandlers.discarding());
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new IllegalStateException("http deliver returned " + response.statusCode());
            }
        } catch (Exception e) {
            throw new IllegalStateException("http deliver failed eventId=" + envelope.getEventId(), e);
        }
    }

    @Override
    public boolean healthy() {
        return joined;
    }

    private String hmac(String body, String secret) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes(java.nio.charset.StandardCharsets.UTF_8), "HmacSHA256"));
        return HexFormat.of().formatHex(mac.doFinal(body.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
}
