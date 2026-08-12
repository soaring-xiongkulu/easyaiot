package com.basiclab.iot.video.service.notify;

import com.basiclab.iot.video.config.VideoProperties;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Extracts notify users from MESSAGE templates (Python {@code _extract_notify_users_from_templates}).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MessageTemplateNotifyUserService {

    private static final Set<String> USERLESS_METHODS = Set.of("http", "webhook");

    private static final Map<String, Integer> METHOD_TO_MSG_TYPE = Map.ofEntries(
            Map.entry("sms", 1),
            Map.entry("email", 3),
            Map.entry("mail", 3),
            Map.entry("wxcp", 4),
            Map.entry("wechat", 4),
            Map.entry("weixin", 4),
            Map.entry("http", 5),
            Map.entry("webhook", 5),
            Map.entry("ding", 6),
            Map.entry("dingtalk", 6),
            Map.entry("feishu", 7),
            Map.entry("lark", 7)
    );

    private final VideoProperties videoProperties;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final HttpClient httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

    public List<Map<String, Object>> extractNotifyUsersFromTemplates(List<Map<String, Object>> channels) {
        Map<String, Map<String, Object>> allUsers = new LinkedHashMap<>();
        if (channels == null || channels.isEmpty()) {
            return List.of();
        }
        for (Map<String, Object> channel : channels) {
            if (isUserlessChannel(channel)) {
                continue;
            }
            String method = channel.get("method") != null ? String.valueOf(channel.get("method")).toLowerCase() : "";
            Object templateIdObj = channel.get("template_id");
            if (templateIdObj == null || String.valueOf(templateIdObj).isBlank()) {
                continue;
            }
            Integer msgType = METHOD_TO_MSG_TYPE.get(method);
            if (msgType == null) {
                continue;
            }
            Map<String, Object> template = fetchTemplateMeta(method, String.valueOf(templateIdObj));
            if (template == null) {
                continue;
            }
            Object userGroupId = template.get("userGroupId");
            if (userGroupId == null) {
                userGroupId = template.get("user_group_id");
            }
            if (userGroupId == null || String.valueOf(userGroupId).isBlank()) {
                continue;
            }
            collectUsersFromGroup(String.valueOf(userGroupId), msgType, allUsers);
        }
        if (!allUsers.isEmpty()) {
            log.info("告警触发时从消息模板提取到 {} 个通知人", allUsers.size());
        }
        return new ArrayList<>(allUsers.values());
    }

    public boolean isRobotFallbackChannel(Map<String, Object> channel) {
        if (channel == null) {
            return false;
        }
        Object templateId = channel.get("template_id");
        if (templateId == null || String.valueOf(templateId).isBlank()) {
            return false;
        }
        String method = channel.get("method") != null ? String.valueOf(channel.get("method")).toLowerCase() : "";
        if (USERLESS_METHODS.contains(method)) {
            return true;
        }
        if (!Set.of("wxcp", "wechat", "weixin", "ding", "dingtalk", "feishu", "lark").contains(method)) {
            return false;
        }
        if (Boolean.TRUE.equals(channel.get("userless"))) {
            return true;
        }
        Map<String, Object> templateMeta = fetchTemplateMeta(method, String.valueOf(templateId));
        if (templateMeta == null) {
            return false;
        }
        Object radioType = templateMeta.get("radioType");
        if (radioType == null) {
            radioType = templateMeta.get("radio_type");
        }
        Object webHook = templateMeta.get("webHook");
        if (webHook == null) {
            webHook = templateMeta.get("web_hook");
        }
        return "群机器人消息".equals(String.valueOf(radioType)) || (webHook != null && !String.valueOf(webHook).isBlank());
    }

    private boolean isUserlessChannel(Map<String, Object> channel) {
        if (Boolean.TRUE.equals(channel.get("userless"))) {
            return true;
        }
        String method = channel.get("method") != null ? String.valueOf(channel.get("method")).toLowerCase() : "";
        return USERLESS_METHODS.contains(method);
    }

    private void collectUsersFromGroup(String userGroupId, Integer msgType, Map<String, Map<String, Object>> allUsers) {
        Map<String, Object> groupResponse = getJson("/admin-api/message/preview/user/group/query?id="
                + encode(userGroupId));
        List<Map<String, Object>> rows = tableRows(groupResponse);
        if (rows.isEmpty()) {
            return;
        }
        Map<String, Object> group = rows.get(0);
        Object tPreviewUsers = group.get("tPreviewUsers");
        if (tPreviewUsers == null) {
            tPreviewUsers = group.get("t_preview_users");
        }
        if (tPreviewUsers instanceof List<?> list && !list.isEmpty()) {
            for (Object userObj : list) {
                mergeUser(castMap(userObj), msgType, allUsers);
            }
            return;
        }
        Object previewUserIds = group.get("previewUserId");
        if (previewUserIds == null) {
            previewUserIds = group.get("preview_user_id");
        }
        if (previewUserIds == null || String.valueOf(previewUserIds).isBlank()) {
            return;
        }
        for (String id : String.valueOf(previewUserIds).split(",")) {
            if (id.isBlank()) {
                continue;
            }
            Map<String, Object> userResponse = getJson("/admin-api/message/preview/user/query?id="
                    + encode(id.trim()) + "&msgType=" + msgType);
            List<Map<String, Object>> userRows = tableRows(userResponse);
            if (!userRows.isEmpty()) {
                mergeUser(userRows.get(0), msgType, allUsers);
            }
        }
    }

    private Map<String, Object> fetchTemplateMeta(String method, String templateId) {
        Integer msgType = METHOD_TO_MSG_TYPE.get(method);
        if (msgType == null || templateId == null || templateId.isBlank()) {
            return null;
        }
        Map<String, Object> response = getJson("/admin-api/message/template/get?id="
                + encode(templateId) + "&msgType=" + msgType);
        if (response == null) {
            return null;
        }
        Object code = response.get("code");
        if (code instanceof Number number && number.intValue() != 0 && number.intValue() != 200) {
            return null;
        }
        Object data = response.get("data");
        return castMap(data);
    }

    private void mergeUser(Map<String, Object> userDetail, Integer defaultMsgType,
                           Map<String, Map<String, Object>> allUsers) {
        if (userDetail == null || userDetail.isEmpty()) {
            return;
        }
        Object id = userDetail.get("id");
        if (id == null || String.valueOf(id).isBlank()) {
            return;
        }
        Integer userMsgType = defaultMsgType;
        Object rawMsgType = userDetail.get("msgType");
        if (rawMsgType instanceof Number number) {
            userMsgType = number.intValue();
        }
        Map<String, Object> userInfo = allUsers.computeIfAbsent(String.valueOf(id), k -> new LinkedHashMap<>());
        userInfo.put("id", id);
        userInfo.put("msgType", userMsgType);
        Object previewUser = userDetail.get("previewUser");
        if (previewUser == null) {
            previewUser = userDetail.get("preview_user");
        }
        if (previewUser != null) {
            userInfo.put("previewUser", previewUser);
            fillContactByMsgType(userInfo, userMsgType, String.valueOf(previewUser));
        }
        if (userDetail.get("name") != null) {
            userInfo.put("name", userDetail.get("name"));
        }
    }

    private static void fillContactByMsgType(Map<String, Object> userInfo, Integer msgType, String previewUser) {
        if (msgType == null || previewUser == null || previewUser.isBlank()) {
            return;
        }
        switch (msgType) {
            case 1 -> {
                userInfo.put("phone", previewUser);
                userInfo.put("mobile", previewUser);
            }
            case 3 -> {
                userInfo.put("email", previewUser);
                userInfo.put("mail", previewUser);
            }
            case 4 -> {
                userInfo.put("wxcp_userid", previewUser);
                userInfo.put("wechat_userid", previewUser);
            }
            case 6 -> {
                userInfo.put("ding_userid", previewUser);
                userInfo.put("dingtalk_userid", previewUser);
            }
            case 7 -> {
                userInfo.put("feishu_userid", previewUser);
                userInfo.put("lark_userid", previewUser);
            }
            default -> {
            }
        }
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> tableRows(Map<String, Object> response) {
        if (response == null) {
            return List.of();
        }
        Object code = response.get("code");
        if (code instanceof Number number && number.intValue() != 0 && number.intValue() != 200) {
            return List.of();
        }
        Object data = response.get("data");
        if (data instanceof List<?> list) {
            List<Map<String, Object>> out = new ArrayList<>();
            for (Object item : list) {
                Map<String, Object> row = castMap(item);
                if (row != null) {
                    out.add(row);
                }
            }
            return out;
        }
        return List.of();
    }

    private Map<String, Object> getJson(String pathWithQuery) {
        try {
            String base = messageServiceBaseUrl();
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(base + pathWithQuery))
                    .timeout(Duration.ofSeconds(5))
                    .header("tenant-id", tenantId())
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200 || response.body() == null) {
                return null;
            }
            return objectMapper.readValue(response.body(), new TypeReference<Map<String, Object>>() {});
        } catch (Exception ex) {
            log.debug("消息服务请求失败 {}: {}", pathWithQuery, ex.getMessage());
            return null;
        }
    }

    private String messageServiceBaseUrl() {
        String url = System.getenv("MESSAGE_SERVICE_URL");
        if (url == null || url.isBlank()) {
            url = videoProperties.getPostProcess().getGatewayUrl();
        }
        if (url == null || url.isBlank()) {
            url = "http://localhost:48080";
        }
        return url.replaceAll("/+$", "");
    }

    private static String tenantId() {
        String tenant = System.getenv("TENANT_ID");
        return tenant != null && !tenant.isBlank() ? tenant : "1";
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castMap(Object obj) {
        if (obj instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                out.put(String.valueOf(entry.getKey()), entry.getValue());
            }
            return out;
        }
        return null;
    }
}
