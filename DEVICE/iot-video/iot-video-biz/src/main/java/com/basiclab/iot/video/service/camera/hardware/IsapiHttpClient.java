package com.basiclab.iot.video.service.camera.hardware;

import lombok.extern.slf4j.Slf4j;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
public final class IsapiHttpClient {

    private static final String USER_AGENT = "hiktools/0.1";
    private static final Pattern LOCK_STATUS = Pattern.compile("<lockStatus>\\s*(\\w+)\\s*</lockStatus>", Pattern.CASE_INSENSITIVE);
    private static final Pattern UNLOCK_TIME = Pattern.compile("<unlockTime>\\s*(\\d+)\\s*</unlockTime>", Pattern.CASE_INSENSITIVE);

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();

    public record Credential(String username, String password) {
    }

    public record Result(int status, String body, String error, Credential usedCredential) {
        public boolean ok() {
            return status == 200 && body != null;
        }
    }

    public Result get(String baseUrl, String path, List<Credential> credentials, double timeoutSeconds) {
        String url = baseUrl.replaceAll("/+$", "") + path;
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofMillis((long) (timeoutSeconds * 1000)))
                    .header("User-Agent", USER_AGENT)
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() == 200) {
                return new Result(200, response.body(), null, null);
            }
            if (response.statusCode() != 401) {
                return new Result(response.statusCode(), response.body(), describeAuthFailure(response.statusCode(), response.body()), null);
            }
            String authHeader = response.headers().firstValue("WWW-Authenticate").orElse("");
            Result last = new Result(401, response.body(), describeAuthFailure(401, response.body()), null);
            for (Credential cred : credentials) {
                String digest = buildDigestAuth("GET", path, cred.username(), cred.password(), authHeader);
                if (digest == null) {
                    continue;
                }
                HttpRequest authed = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .timeout(Duration.ofMillis((long) (timeoutSeconds * 1000)))
                        .header("User-Agent", USER_AGENT)
                        .header("Authorization", digest)
                        .GET()
                        .build();
                HttpResponse<String> authedResponse = httpClient.send(authed, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
                if (authedResponse.statusCode() == 200) {
                    return new Result(200, authedResponse.body(), null, cred);
                }
                last = new Result(authedResponse.statusCode(), authedResponse.body(),
                        describeAuthFailure(authedResponse.statusCode(), authedResponse.body()), cred);
            }
            return last;
        } catch (Exception ex) {
            log.debug("ISAPI GET {} failed: {}", url, ex.getMessage());
            return new Result(-1, null, ex.getMessage(), null);
        }
    }

    public static List<Credential> parseCredentials(String username, String password, List<Map<String, Object>> credentials) {
        List<Credential> out = new ArrayList<>();
        if (credentials != null) {
            for (Map<String, Object> item : credentials) {
                if (item == null) {
                    continue;
                }
                String user = str(item.get("username"));
                if (!user.isEmpty()) {
                    out.add(new Credential(user, str(item.get("password"))));
                }
            }
        }
        if (out.isEmpty()) {
            String user = str(username);
            if (!user.isEmpty()) {
                out.add(new Credential(user, password != null ? password : ""));
            }
        }
        return out;
    }

    public static String schemeForPort(int port) {
        return port == 443 || port == 8443 ? "https" : "http";
    }

    public static String xmlText(String block, String tag) {
        Matcher matcher = Pattern.compile(
                "<(?:[\\w-]+:)?" + Pattern.quote(tag) + ">\\s*([^<]*?)\\s*</(?:[\\w-]+:)?" + Pattern.quote(tag) + ">",
                Pattern.CASE_INSENSITIVE | Pattern.DOTALL
        ).matcher(block);
        return matcher.find() ? matcher.group(1).trim() : "";
    }

    private static String describeAuthFailure(int status, String body) {
        if (status != 401) {
            return status > 0 ? "HTTP " + status : "request failed";
        }
        String text = body != null ? body : "";
        Matcher lock = LOCK_STATUS.matcher(text);
        if (lock.find() && "lock".equalsIgnoreCase(lock.group(1))) {
            Matcher unlock = UNLOCK_TIME.matcher(text);
            int sec = unlock.find() ? Integer.parseInt(unlock.group(1)) : 0;
            int mins = Math.max(1, (sec + 59) / 60);
            return "NVR 账号已锁定，请约 " + mins + " 分钟后重试或在 NVR Web 界面解除锁定";
        }
        if (text.contains("<userCheck>") || text.contains("Unauthorized")) {
            return "NVR 凭证认证失败（401），请检查用户名和密码";
        }
        return "HTTP 401";
    }

    private static String buildDigestAuth(String method, String uri, String username, String password, String authInfo) {
        if (authInfo == null || authInfo.isBlank()) {
            return null;
        }
        Map<String, String> parts = new HashMap<>();
        String cleaned = authInfo.replaceFirst("(?i)^Digest\\s+", "").trim();
        for (String part : cleaned.split(",")) {
            int eq = part.indexOf('=');
            if (eq > 0) {
                String key = part.substring(0, eq).trim();
                String value = part.substring(eq + 1).trim().replace("\"", "");
                parts.put(key, value);
            }
        }
        String realm = parts.getOrDefault("realm", "");
        String nonce = parts.getOrDefault("nonce", "");
        String qop = parts.getOrDefault("qop", "");
        String opaque = parts.getOrDefault("opaque", "");
        String ha1 = md5(username + ":" + realm + ":" + password);
        String ha2 = md5(method + ":" + uri);
        String responseHash;
        String nc = "00000001";
        String cnonce = md5(String.valueOf(System.nanoTime())).substring(0, 8);
        if (qop != null && (qop.contains("auth") || "auth".equalsIgnoreCase(qop))) {
            responseHash = md5(ha1 + ":" + nonce + ":" + nc + ":" + cnonce + ":auth:" + ha2);
            return "Digest username=\"" + username + "\", realm=\"" + realm + "\", nonce=\"" + nonce
                    + "\", uri=\"" + uri + "\", qop=auth, nc=" + nc + ", cnonce=\"" + cnonce
                    + "\", response=\"" + responseHash + "\"" + (opaque.isBlank() ? "" : ", opaque=\"" + opaque + "\"");
        }
        responseHash = md5(ha1 + ":" + nonce + ":" + ha2);
        return "Digest username=\"" + username + "\", realm=\"" + realm + "\", nonce=\"" + nonce
                + "\", uri=\"" + uri + "\", response=\"" + responseHash + "\"";
    }

    private static String md5(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("MD5");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format(Locale.ROOT, "%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException(ex);
        }
    }

    private static String str(Object value) {
        return value != null ? String.valueOf(value).trim() : "";
    }
}
