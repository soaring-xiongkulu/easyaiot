package com.basiclab.iot.sink.service.impl;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.PlateMatchingMessage;
import com.basiclab.iot.sink.service.PlateMatchingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 车牌匹配业务实现：调用 VIDEO 模块异步匹配接口
 */
@Slf4j
@Service
public class PlateMatchingServiceImpl implements PlateMatchingService {

    private static final RestTemplate MATCHING_HTTP = createMatchingRestTemplate();

    @Autowired(required = false)
    private KafkaTemplate<String, String> iotKafkaTemplate;

    @Value("${basiclab.video.service-url:http://localhost:48080}")
    private String videoServiceUrl;

    @Value("${basiclab.video.api-prefix:/admin-api/video}")
    private String videoApiPrefix;

    @Value("${spring.kafka.plate-matching.result-topic:iot-plate-matching-result}")
    private String resultTopic;

    @Override
    public void process(PlateMatchingMessage message) {
        if (message == null) {
            throw new IllegalArgumentException("车牌匹配消息为空");
        }
        if (message.getTaskId() == null) {
            throw new IllegalArgumentException("taskId 不能为空");
        }
        if (message.getPlateNo() == null || message.getPlateNo().isEmpty()) {
            throw new IllegalArgumentException("plateNo 不能为空");
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("taskId", message.getTaskId());
        payload.put("taskName", message.getTaskName());
        payload.put("taskType", message.getTaskType());
        payload.put("deviceId", message.getDeviceId());
        payload.put("deviceName", message.getDeviceName());
        payload.put("libraryId", message.getLibraryId());
        payload.put("libraryName", message.getLibraryName());
        payload.put("plateNo", message.getPlateNo());
        payload.put("plateColor", message.getPlateColor());
        payload.put("plateImagePath", message.getPlateImagePath());
        payload.put("detectConf", message.getDetectConf());
        payload.put("alertId", message.getAlertId());
        payload.put("correlationId", message.getCorrelationId());
        payload.put("rect", message.getRect());
        payload.put("landmarks", message.getLandmarks());

        String url = normalizeBaseUrl(videoServiceUrl) + normalizeApiPrefix(videoApiPrefix) + "/plate/matching/process";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(payload, headers);

        log.info("开始调用车牌匹配: deviceId={}, libraryId={}, plateNo={}",
                message.getDeviceId(), message.getLibraryId(), message.getPlateNo());

        ResponseEntity<String> response = MATCHING_HTTP.postForEntity(url, entity, String.class);
        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new IllegalStateException("VIDEO 车牌匹配接口返回异常: status=" + response.getStatusCodeValue()
                    + ", body=" + response.getBody());
        }

        log.info("车牌匹配处理完成: deviceId={}, libraryId={}, plateNo={}, response={}",
                message.getDeviceId(), message.getLibraryId(), message.getPlateNo(), response.getBody());

        publishResult(message, response.getBody());
    }

    private void publishResult(PlateMatchingMessage message, String processResponseBody) {
        if (iotKafkaTemplate == null) {
            return;
        }
        try {
            Map<String, Object> result = new HashMap<>();
            result.put("deviceId", message.getDeviceId());
            result.put("libraryId", message.getLibraryId());
            result.put("plateNo", message.getPlateNo());
            result.put("plateColor", message.getPlateColor());
            result.put("plateImagePath", message.getPlateImagePath());
            result.put("taskId", message.getTaskId());
            result.put("processResponse", processResponseBody);
            result.put("timestamp", message.getTimestamp());
            iotKafkaTemplate.send(resultTopic, message.getDeviceId(), JsonUtils.toJsonString(result));
        } catch (Exception e) {
            log.warn("发送车牌匹配结果到 Kafka 失败: deviceId={}, plateNo={}, error={}",
                    message.getDeviceId(), message.getPlateNo(), e.getMessage(), e);
        }
    }

    private static RestTemplate createMatchingRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10_000);
        factory.setReadTimeout(30_000);
        return new RestTemplate(factory);
    }

    private static String normalizeBaseUrl(String baseUrl) {
        if (baseUrl == null || baseUrl.isEmpty()) {
            return "http://localhost:48080";
        }
        return baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
    }

    private static String normalizeApiPrefix(String apiPrefix) {
        if (apiPrefix == null || apiPrefix.isEmpty()) {
            return "/admin-api/video";
        }
        return apiPrefix.startsWith("/") ? apiPrefix : "/" + apiPrefix;
    }
}
