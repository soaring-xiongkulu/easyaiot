package com.basiclab.iot.video.service.camera.hardware;

import lombok.extern.slf4j.Slf4j;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
public final class OnvifSoapClient {

    private static final String SOAP_NS = "http://www.w3.org/2003/05/soap-envelope";
    private static final String WSSE_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd";
    private static final String WSU_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-ws-security-utility-1.0.xsd";

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    public record Session(String deviceServiceUrl, String mediaServiceUrl, String ptzServiceUrl,
                          String profileToken, String ptzConfigurationToken) {
    }

    public Session connect(String ip, int port, String username, String password, int timeoutSeconds) throws OnvifException {
        String deviceUrl = "http://" + ip + ":" + port + "/onvif/device_service";
        String capabilities = invoke(deviceUrl, "tds", "http://www.onvif.org/ver10/device/wsdl",
                "GetCapabilities", "<tds:Category>All</tds:Category>", username, password, timeoutSeconds);
        String mediaUrl = firstXAddr(capabilities, "Media");
        if (mediaUrl == null || mediaUrl.isBlank()) {
            mediaUrl = "http://" + ip + ":" + port + "/onvif/media_service";
        }
        String ptzUrl = firstXAddr(capabilities, "PTZ");
        String profiles = invoke(mediaUrl, "trt", "http://www.onvif.org/ver10/media/wsdl",
                "GetProfiles", "", username, password, timeoutSeconds);
        String profileToken = xmlValue(profiles, "token");
        if (profileToken == null || profileToken.isBlank()) {
            throw new OnvifException("未找到有效的媒体配置文件");
        }
        String ptzToken = xmlValue(profiles, "PTZConfiguration") != null
                ? xmlNestedValue(profiles, "PTZConfiguration", "token")
                : xmlValue(profiles, "ConfigurationToken");
        return new Session(deviceUrl, mediaUrl, ptzUrl, profileToken, ptzToken);
    }

    public Map<String, Object> getDeviceInformation(Session session, String username, String password, int timeoutSeconds)
            throws OnvifException {
        String body = invoke(session.deviceServiceUrl(), "tds", "http://www.onvif.org/ver10/device/wsdl",
                "GetDeviceInformation", "", username, password, timeoutSeconds);
        Map<String, Object> info = new LinkedHashMap<>();
        info.put("manufacturer", xmlValue(body, "Manufacturer"));
        info.put("model", xmlValue(body, "Model"));
        info.put("firmware_version", xmlValue(body, "FirmwareVersion"));
        info.put("serial_number", xmlValue(body, "SerialNumber"));
        info.put("hardware_id", xmlValue(body, "HardwareId"));
        return info;
    }

    public String getMacAddress(Session session, String username, String password, int timeoutSeconds) throws OnvifException {
        String body = invoke(session.deviceServiceUrl(), "tds", "http://www.onvif.org/ver10/device/wsdl",
                "GetNetworkInterfaces", "", username, password, timeoutSeconds);
        return xmlValue(body, "HwAddress");
    }

    public String getStreamUri(Session session, String username, String password, int timeoutSeconds) throws OnvifException {
        String payload = "<trt:ProfileToken>" + escape(session.profileToken()) + "</trt:ProfileToken>"
                + "<trt:StreamSetup><tt:Stream>RTP-Unicast</tt:Stream>"
                + "<tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport></trt:StreamSetup>";
        String body = invoke(session.mediaServiceUrl(), "trt", "http://www.onvif.org/ver10/media/wsdl",
                "GetStreamUri", payload, username, password, timeoutSeconds, "http://www.onvif.org/ver10/schema");
        return xmlValue(body, "Uri");
    }

    public String getSnapshotUri(Session session, String username, String password, int timeoutSeconds) throws OnvifException {
        String payload = "<trt:ProfileToken>" + escape(session.profileToken()) + "</trt:ProfileToken>";
        String body = invoke(session.mediaServiceUrl(), "trt", "http://www.onvif.org/ver10/media/wsdl",
                "GetSnapshotUri", payload, username, password, timeoutSeconds);
        return xmlValue(body, "Uri");
    }

    public void continuousMove(Session session, double x, double y, double z,
                               String username, String password, int timeoutSeconds) throws OnvifException {
        if (session.ptzServiceUrl() == null || session.ptzServiceUrl().isBlank()) {
            throw new OnvifException("该设备不支持云台/预置点");
        }
        String token = session.ptzConfigurationToken() != null ? session.ptzConfigurationToken() : session.profileToken();
        String payload = "<tptz:ProfileToken>" + escape(session.profileToken()) + "</tptz:ProfileToken>"
                + "<tptz:Velocity><tt:PanTilt x=\"" + x + "\" y=\"" + y + "\"/>"
                + (z != 0 ? "<tt:Zoom x=\"" + z + "\"/>" : "")
                + "</tptz:Velocity>";
        invoke(session.ptzServiceUrl(), "tptz", "http://www.onvif.org/ver10/ptz/wsdl",
                "ContinuousMove", payload, username, password, timeoutSeconds, "http://www.onvif.org/ver10/schema");
        try {
            Thread.sleep((long) (Math.max(Math.abs(x), Math.max(Math.abs(y), Math.abs(z))) * 1000));
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
        }
        stop(session, username, password, timeoutSeconds);
    }

    public void stop(Session session, String username, String password, int timeoutSeconds) throws OnvifException {
        if (session.ptzServiceUrl() == null || session.ptzServiceUrl().isBlank()) {
            return;
        }
        String payload = "<tptz:ProfileToken>" + escape(session.profileToken()) + "</tptz:ProfileToken>";
        invoke(session.ptzServiceUrl(), "tptz", "http://www.onvif.org/ver10/ptz/wsdl",
                "Stop", payload, username, password, timeoutSeconds);
    }

    public List<Map<String, String>> listPresets(Session session, String username, String password, int timeoutSeconds)
            throws OnvifException {
        if (session.ptzServiceUrl() == null || session.ptzServiceUrl().isBlank()) {
            throw new OnvifException("该设备不支持云台/预置点");
        }
        String payload = "<tptz:ProfileToken>" + escape(session.profileToken()) + "</tptz:ProfileToken>";
        String body = invoke(session.ptzServiceUrl(), "tptz", "http://www.onvif.org/ver10/ptz/wsdl",
                "GetPresets", payload, username, password, timeoutSeconds);
        List<Map<String, String>> presets = new ArrayList<>();
        Matcher matcher = Pattern.compile("<(?:[\\w-]+:)?Preset\\b[^>]*>(.*?)</(?:[\\w-]+:)?Preset>", Pattern.CASE_INSENSITIVE | Pattern.DOTALL)
                .matcher(body);
        int idx = 1;
        while (matcher.find()) {
            String block = matcher.group(1);
            String token = xmlAttr(matcher.group(0), "token");
            if (token == null || token.isBlank()) {
                token = xmlValue(block, "token");
            }
            if (token == null || token.isBlank()) {
                continue;
            }
            String name = xmlValue(block, "Name");
            if (name == null || name.isBlank()) {
                name = "预置点 " + idx;
            }
            presets.add(Map.of("token", token, "name", name));
            idx++;
        }
        return presets;
    }

    public String setPreset(Session session, String name, String presetToken,
                            String username, String password, int timeoutSeconds) throws OnvifException {
        if (session.ptzServiceUrl() == null || session.ptzServiceUrl().isBlank()) {
            throw new OnvifException("该设备不支持云台/预置点");
        }
        StringBuilder payload = new StringBuilder();
        payload.append("<tptz:ProfileToken>").append(escape(session.profileToken())).append("</tptz:ProfileToken>");
        payload.append("<tptz:PresetName>").append(escape(name)).append("</tptz:PresetName>");
        if (presetToken != null && !presetToken.isBlank()) {
            payload.append("<tptz:PresetToken>").append(escape(presetToken)).append("</tptz:PresetToken>");
        }
        String body = invoke(session.ptzServiceUrl(), "tptz", "http://www.onvif.org/ver10/ptz/wsdl",
                "SetPreset", payload.toString(), username, password, timeoutSeconds);
        String token = xmlValue(body, "PresetToken");
        return token != null && !token.isBlank() ? token : presetToken;
    }

    public void gotoPreset(Session session, String presetToken, String username, String password, int timeoutSeconds)
            throws OnvifException {
        if (session.ptzServiceUrl() == null || session.ptzServiceUrl().isBlank()) {
            throw new OnvifException("该设备不支持云台/预置点");
        }
        String payload = "<tptz:ProfileToken>" + escape(session.profileToken()) + "</tptz:ProfileToken>"
                + "<tptz:PresetToken>" + escape(presetToken) + "</tptz:PresetToken>";
        invoke(session.ptzServiceUrl(), "tptz", "http://www.onvif.org/ver10/ptz/wsdl",
                "GotoPreset", payload, username, password, timeoutSeconds);
    }

    public void removePreset(Session session, String presetToken, String username, String password, int timeoutSeconds)
            throws OnvifException {
        if (session.ptzServiceUrl() == null || session.ptzServiceUrl().isBlank()) {
            throw new OnvifException("该设备不支持云台/预置点");
        }
        String payload = "<tptz:ProfileToken>" + escape(session.profileToken()) + "</tptz:ProfileToken>"
                + "<tptz:PresetToken>" + escape(presetToken) + "</tptz:PresetToken>";
        invoke(session.ptzServiceUrl(), "tptz", "http://www.onvif.org/ver10/ptz/wsdl",
                "RemovePreset", payload, username, password, timeoutSeconds);
    }

    public byte[] fetchSnapshot(String snapshotUri, String username, String password, int timeoutSeconds) throws OnvifException {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(snapshotUri))
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .GET();
            if (username != null && !username.isBlank()) {
                String userInfo = username + ":" + (password != null ? password : "");
                builder.header("Authorization", "Basic " + Base64.getEncoder().encodeToString(userInfo.getBytes(StandardCharsets.UTF_8)));
            }
            HttpResponse<byte[]> response = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofByteArray());
            if (response.statusCode() != 200 || response.body() == null || response.body().length == 0) {
                throw new OnvifException("ONVIF快照请求失败: HTTP " + response.statusCode());
            }
            return response.body();
        } catch (OnvifException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new OnvifException("ONVIF快照请求失败: " + ex.getMessage());
        }
    }

    private String invoke(String serviceUrl, String prefix, String namespace, String action, String innerBody,
                          String username, String password, int timeoutSeconds, String... extraNamespaces) throws OnvifException {
        String envelope = buildEnvelope(prefix, namespace, action, innerBody, username, password, extraNamespaces);
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(serviceUrl))
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .header("Content-Type", "application/soap+xml; charset=utf-8")
                    .POST(HttpRequest.BodyPublishers.ofString(envelope, StandardCharsets.UTF_8))
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            String body = response.body() != null ? response.body() : "";
            if (response.statusCode() >= 400 || body.contains("soap:Fault") || body.contains("Fault>")) {
                String fault = xmlValue(body, "Reason") != null ? xmlValue(body, "Reason") : xmlValue(body, "Text");
                throw new OnvifException(fault != null && !fault.isBlank() ? fault : "ONVIF 请求失败: HTTP " + response.statusCode());
            }
            return body;
        } catch (OnvifException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new OnvifException("ONVIF 连接失败: " + ex.getMessage());
        }
    }

    private static String buildEnvelope(String prefix, String namespace, String action, String innerBody,
                                          String username, String password, String... extraNamespaces) {
        StringBuilder ns = new StringBuilder();
        ns.append(" xmlns:s=\"").append(SOAP_NS).append("\"");
        ns.append(" xmlns:").append(prefix).append("=\"").append(namespace).append("\"");
        ns.append(" xmlns:wsse=\"").append(WSSE_NS).append("\"");
        ns.append(" xmlns:wsu=\"").append(WSU_NS).append("\"");
        if (extraNamespaces != null && extraNamespaces.length > 0) {
            ns.append(" xmlns:tt=\"").append(extraNamespaces[0]).append("\"");
        } else {
            ns.append(" xmlns:tt=\"http://www.onvif.org/ver10/schema\"");
        }
        String created = Instant.now().toString();
        byte[] nonceBytes = new byte[16];
        new SecureRandom().nextBytes(nonceBytes);
        String nonce = Base64.getEncoder().encodeToString(nonceBytes);
        String digest = passwordDigest(nonceBytes, created, password != null ? password : "");
        String security = username != null && !username.isBlank()
                ? "<wsse:Security s:mustUnderstand=\"1\"><wsse:UsernameToken>"
                + "<wsse:Username>" + escape(username) + "</wsse:Username>"
                + "<wsse:Password Type=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest\">"
                + digest + "</wsse:Password>"
                + "<wsse:Nonce EncodingType=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary\">"
                + nonce + "</wsse:Nonce>"
                + "<wsu:Created>" + created + "</wsu:Created>"
                + "</wsse:UsernameToken></wsse:Security>"
                : "";
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                + "<s:Envelope" + ns + ">"
                + "<s:Header>" + security + "</s:Header>"
                + "<s:Body><" + prefix + ":" + action + ">" + innerBody + "</" + prefix + ":" + action + "></s:Body>"
                + "</s:Envelope>";
    }

    private static String passwordDigest(byte[] nonce, String created, String password) {
        try {
            MessageDigest sha1 = MessageDigest.getInstance("SHA-1");
            sha1.update(nonce);
            sha1.update(created.getBytes(StandardCharsets.UTF_8));
            sha1.update(password.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(sha1.digest());
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException(ex);
        }
    }

    private static String firstXAddr(String xml, String capabilityName) {
        Matcher section = Pattern.compile(
                "<(?:[\\w-]+:)?" + capabilityName + "\\b[^>]*>(.*?)</(?:[\\w-]+:)?" + capabilityName + ">",
                Pattern.CASE_INSENSITIVE | Pattern.DOTALL
        ).matcher(xml);
        if (!section.find()) {
            return null;
        }
        return xmlValue(section.group(1), "XAddr");
    }

    private static String xmlValue(String xml, String tag) {
        if (xml == null) {
            return null;
        }
        Matcher matcher = Pattern.compile(
                "<(?:[\\w-]+:)?" + Pattern.quote(tag) + "(?:\\s[^>]*)?>([^<]*)</(?:[\\w-]+:)?" + Pattern.quote(tag) + "\\s*>",
                Pattern.CASE_INSENSITIVE
        ).matcher(xml);
        return matcher.find() ? matcher.group(1).trim() : null;
    }

    private static String xmlNestedValue(String xml, String parentTag, String childTag) {
        Matcher parent = Pattern.compile(
                "<(?:[\\w-]+:)?" + parentTag + "\\b[^>]*>(.*?)</(?:[\\w-]+:)?" + parentTag + ">",
                Pattern.CASE_INSENSITIVE | Pattern.DOTALL
        ).matcher(xml);
        if (!parent.find()) {
            return null;
        }
        return xmlValue(parent.group(1), childTag);
    }

    private static String xmlAttr(String tagBlock, String attr) {
        Matcher matcher = Pattern.compile(attr + "=\"([^\"]+)\"", Pattern.CASE_INSENSITIVE).matcher(tagBlock);
        return matcher.find() ? matcher.group(1) : null;
    }

    private static String escape(String value) {
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
    }

    public static class OnvifException extends Exception {
        public OnvifException(String message) {
            super(message);
        }
    }
}
