package com.basiclab.iot.message.sendlogic.msgsender;

import cn.hutool.core.util.ArrayUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.http.Header;
import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.model.HttpSendResult;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.domain.model.bean.HttpMsg;
import com.basiclab.iot.message.sendlogic.msgmaker.HttpMsgMaker;
import com.basiclab.iot.message.service.MessageConfigService;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import java.net.HttpCookie;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * Http消息发送器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Slf4j
@Component
public class HttpMsgSender implements IMsgSender {

    @Autowired
    private HttpMsgMaker httpMsgMaker;

    private volatile Proxy proxy;
    private volatile OkHttpClient okHttpClient;

    @Autowired
    private MessageConfigService messageConfigService;

    // 创建独立的线程池，避免使用Tomcat线程
    private final Executor asyncExecutor = Executors.newFixedThreadPool(10);

    @Override
    public HttpSendResult send(String msgId) {
        log.info("HTTP发送开始, msgId: {}", msgId);
        try {
            HttpSendResult result = sendUseOkHttp(msgId);
            log.info("HTTP发送完成, msgId: {}, success: {}", msgId, result.isSuccess());
            return result;
        } catch (Exception e) {
            log.error("HTTP发送过程中发生异常, msgId: {}, error: {}", msgId, e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 直接使用HttpMsg对象发送（不从数据库读取）
     * 用于支持前端直接传递HTTP参数的情况
     */
    public HttpSendResult sendWithHttpMsg(HttpMsg httpMsg) {
        log.info("使用HttpMsg对象直接发送, msgName: {}, method: {}, url: {}",
                httpMsg.getMsgName(), httpMsg.getMethod(), httpMsg.getUrl());
        try {
            // 使用独立的线程池执行，避免死锁
            CompletableFuture<HttpSendResult> future = CompletableFuture.supplyAsync(() -> {
                try {
                    // 先尝试 Hutool
                    HttpSendResult hutoolResult = sendUseHutoolWithMsg(httpMsg);
                    if (hutoolResult.isSuccess()) {
                        log.info("Hutool 发送成功");
                        return hutoolResult;
                    }

                    log.info("Hutool 发送失败，尝试 OkHttp");
                    return sendUseOkHttpWithMsg(httpMsg);
                } catch (Exception e) {
                    log.error("异步发送失败: {}", e.getMessage());
                    HttpSendResult result = new HttpSendResult();
                    result.setMsgName(httpMsg.getMsgName());
                    result.setSuccess(false);
                    result.setInfo("异步发送失败: " + e.getMessage());
                    return result;
                }
            }, asyncExecutor);

            // 等待结果，设置超时
            HttpSendResult result = future.get(30, TimeUnit.SECONDS);
            log.info("HTTP发送完成, msgName: {}, success: {}", httpMsg.getMsgName(), result.isSuccess());
            return result;

        } catch (Exception e) {
            log.error("HTTP发送过程中发生异常, msgName: {}, error: {}", httpMsg.getMsgName(), e.getMessage(), e);
            HttpSendResult result = new HttpSendResult();
            result.setMsgName(httpMsg.getMsgName());
            result.setSuccess(false);
            result.setInfo("发送异常: " + e.getMessage());
            return result;
        }
    }

    /**
     * 异步发送方法
     */
    @Async
    public CompletableFuture<HttpSendResult> asyncSendWithHttpMsg(HttpMsg httpMsg) {
        return CompletableFuture.supplyAsync(() -> sendWithHttpMsg(httpMsg), asyncExecutor);
    }

    @Override
    public SendResult asyncSend(String[] msgData) {
        return null;
    }

    /**
     * 直接使用HttpMsg对象发送（Hutool实现，用于OPTIONS等方法）
     */
    public HttpSendResult sendUseHutoolWithMsg(HttpMsg httpMsg) {
        HttpSendResult sendResult = new HttpSendResult();
        sendResult.setMsgName(httpMsg.getMsgName());
        HttpResponse httpResponse;
        try {
            log.debug("使用Hutool发送HTTP请求, url: {}, method: {}", httpMsg.getUrl(), httpMsg.getMethod());

            // 如果请求的是本地服务，使用127.0.0.1而不是localhost
            String finalUrl = httpMsg.getUrl();
            if (isLocalRequest(finalUrl)) {
                finalUrl = finalUrl.replace("localhost:", "127.0.0.1:");
                log.debug("本地请求，使用127.0.0.1: {}", finalUrl);
            }

            HttpRequest httpRequest;
            switch (httpMsg.getMethod().toUpperCase()) {
                case "GET":
                    httpRequest = HttpRequest.get(finalUrl);
                    break;
                case "POST":
                    httpRequest = HttpRequest.post(finalUrl);
                    break;
                case "PUT":
                    httpRequest = HttpRequest.put(finalUrl);
                    break;
                case "PATCH":
                    httpRequest = HttpRequest.patch(finalUrl);
                    break;
                case "DELETE":
                    httpRequest = HttpRequest.delete(finalUrl);
                    break;
                case "HEAD":
                    httpRequest = HttpRequest.head(finalUrl);
                    break;
                case "OPTIONS":
                    httpRequest = HttpRequest.options(finalUrl);
                    break;
                default:
                    httpRequest = HttpRequest.get(finalUrl).form(httpMsg.getParamMap());
            }

            // 设置较短的超时时间，避免阻塞
            httpRequest.timeout(10000); // 10秒

            // 优先使用body，只有当body为空时才使用params
            if (StringUtils.isNotEmpty(httpMsg.getBody())) {
                log.debug("设置请求体, length: {}", httpMsg.getBody().length());
                httpRequest.body(httpMsg.getBody());
            } else if (httpMsg.getParamMap() != null && !httpMsg.getParamMap().isEmpty()) {
                log.debug("设置表单参数, paramCount: {}", httpMsg.getParamMap().size());
                httpRequest.form(httpMsg.getParamMap());
            }

            // 设置请求头
            if (httpMsg.getHeaderMap() != null && !httpMsg.getHeaderMap().isEmpty()) {
                log.debug("设置请求头, headerCount: {}", httpMsg.getHeaderMap().size());
                for (Map.Entry<String, Object> entry : httpMsg.getHeaderMap().entrySet()) {
                    httpRequest.header(entry.getKey(), (String) entry.getValue());
                }
            }

            // 设置Content-Type
            if (StringUtils.isNotEmpty(httpMsg.getBody())) {
                String contentType = httpMsg.getBodyType();
                if (StringUtils.isEmpty(contentType)) {
                    contentType = "application/json";
                }
                httpRequest.header("Content-Type", contentType + "; charset=utf-8");
            }

            // 添加User-Agent
            httpRequest.header("User-Agent", "Hutool-HTTP");

            // 添加Accept
            httpRequest.header("Accept", "application/json");

            if (httpMsg.getCookies() != null && !httpMsg.getCookies().isEmpty()) {
                HttpCookie[] cookies = ArrayUtil.toArray(httpMsg.getCookies(), HttpCookie.class);
                httpRequest.cookie(cookies);
            }

            log.info("Hutool发送请求: {} {}", httpMsg.getMethod(), finalUrl);

            httpResponse = httpRequest.execute();

            log.info("Hutool响应: status={}, length={}",
                    httpResponse.getStatus(), httpResponse.body().length());

            if (!httpResponse.isOk()) {
                sendResult.setSuccess(false);
                sendResult.setInfo("HTTP " + httpResponse.getStatus() + ": " + httpResponse.body());
                return sendResult;
            }

        } catch (Exception e) {
            log.error("Hutool发送异常: {}", e.getMessage());
            sendResult.setSuccess(false);
            sendResult.setInfo("Hutool发送异常: " + e.getMessage());
            return sendResult;
        }

        StringBuilder headerBuilder = StrUtil.builder();
        for (Map.Entry<String, List<String>> entry : httpResponse.headers().entrySet()) {
            headerBuilder.append(entry.getKey()).append(": ").append(entry.getValue()).append(StrUtil.CRLF);
        }
        sendResult.setHeaders(headerBuilder.toString());

        String body = httpResponse.body();
        sendResult.setInfo(body);
        if (body != null && body.startsWith("{") && body.endsWith("}")) {
            try {
                body = JSONUtil.toJsonPrettyStr(body);
            } catch (Exception e) {
                log.error("JSON格式化错误: {}", e.toString());
            }
        }
        sendResult.setBody(body);

        StringBuilder cookiesBuilder = StrUtil.builder();
        List<String> headerList = httpResponse.headerList(Header.SET_COOKIE.toString());
        if (headerList != null) {
            for (String cookieStr : headerList) {
                cookiesBuilder.append(cookieStr).append(StrUtil.CRLF);
            }
        }

        sendResult.setCookies(cookiesBuilder.toString());
        sendResult.setSuccess(true);

        return sendResult;
    }

    /**
     * 直接使用HttpMsg对象发送（不从数据库读取）
     */
    public HttpSendResult sendUseOkHttpWithMsg(HttpMsg httpMsg) {
        log.info("开始使用OkHttp发送消息（直接使用HttpMsg对象）, msgName: {}, method: {}, url: {}",
                httpMsg.getMsgName(), httpMsg.getMethod(), httpMsg.getUrl());
        HttpSendResult sendResult = new HttpSendResult();
        Response response = null;
        try {
            log.debug("准备获取OkHttpClient");
            OkHttpClient okHttpClient = getOkHttpClient();
            log.debug("OkHttpClient获取成功");

            sendResult.setMsgName(httpMsg.getMsgName());

            log.debug("开始构建HTTP请求");
            Request.Builder requestBuilder = new Request.Builder();

            RequestBody requestBody = null;
            // 优先使用body，只有当body为空时才使用params
            if (!"GET".equals(httpMsg.getMethod()) &&
                    httpMsg.getBody() != null && !httpMsg.getBody().trim().isEmpty()) {
                log.info("构建JSON/文本请求体, bodyType: {}, bodyLength: {}",
                        httpMsg.getBodyType(), httpMsg.getBody().length());
                String bodyType = httpMsg.getBodyType() != null ? httpMsg.getBodyType() : "application/json";
                MediaType mediaType = MediaType.parse(bodyType + "; charset=utf-8");
                requestBody = RequestBody.create(httpMsg.getBody(), mediaType);
            } else if (!"GET".equals(httpMsg.getMethod()) &&
                    httpMsg.getParamMap() != null && !httpMsg.getParamMap().isEmpty()) {
                log.debug("构建表单请求体, paramCount: {}", httpMsg.getParamMap().size());
                FormBody.Builder formBodyBuilder = new FormBody.Builder();
                for (Map.Entry<String, Object> paramEntry : httpMsg.getParamMap().entrySet()) {
                    formBodyBuilder.add(paramEntry.getKey(), (String) paramEntry.getValue());
                }
                requestBody = formBodyBuilder.build();
            } else if (!"GET".equals(httpMsg.getMethod())) {
                // POST/PUT/PATCH等请求，如果没有body和params，创建一个空的JSON body
                log.debug("构建空请求体, method: {}", httpMsg.getMethod());
                MediaType mediaType = MediaType.parse("application/json; charset=utf-8");
                requestBody = RequestBody.create("{}", mediaType);
            }

            // 添加必要的请求头
            if (requestBody != null) {
                // 自动添加 Content-Type 头
                String contentType = httpMsg.getBodyType();
                if (StringUtils.isEmpty(contentType) && httpMsg.getBody() != null
                        && httpMsg.getBody().trim().startsWith("{")) {
                    contentType = "application/json";
                }
                if (StringUtils.isNotEmpty(contentType)) {
                    requestBuilder.addHeader("Content-Type", contentType + "; charset=utf-8");
                }
            }

            // 添加 User-Agent 头
            requestBuilder.addHeader("User-Agent", "OkHttpClient");

            // 添加 Accept 头
            requestBuilder.addHeader("Accept", "application/json");

            // 添加配置的请求头
            if (httpMsg.getHeaderMap() != null && !httpMsg.getHeaderMap().isEmpty()) {
                log.debug("添加请求头, headerCount: {}", httpMsg.getHeaderMap().size());
                for (Map.Entry<String, Object> headerEntry : httpMsg.getHeaderMap().entrySet()) {
                    requestBuilder.addHeader(headerEntry.getKey(), (String) headerEntry.getValue());
                }
            }
            if (httpMsg.getCookies() != null && !httpMsg.getCookies().isEmpty()) {
                log.debug("添加Cookie, cookieCount: {}", httpMsg.getCookies().size());
                requestBuilder.addHeader(Header.COOKIE.toString(), cookieHeader(httpMsg.getCookies()));
            }

            // 如果请求的是本地服务，使用127.0.0.1而不是localhost
            String finalUrl = httpMsg.getUrl();
            if (isLocalRequest(finalUrl)) {
                finalUrl = finalUrl.replace("localhost:", "127.0.0.1:");
                log.debug("本地请求，使用127.0.0.1: {}", finalUrl);
            }

            log.debug("设置HTTP方法和URL, method: {}, url: {}", httpMsg.getMethod(), finalUrl);

            switch (httpMsg.getMethod().toUpperCase()) {
                case "GET":
                    HttpUrl.Builder urlBuilder = HttpUrl.parse(finalUrl).newBuilder();
                    if (httpMsg.getParamMap() != null && !httpMsg.getParamMap().isEmpty()) {
                        for (Map.Entry<String, Object> paramEntry : httpMsg.getParamMap().entrySet()) {
                            urlBuilder.addQueryParameter(paramEntry.getKey(), (String) paramEntry.getValue());
                        }
                    }
                    requestBuilder.url(urlBuilder.build()).get();
                    break;
                case "POST":
                    requestBuilder.url(finalUrl).post(requestBody);
                    break;
                case "PUT":
                    requestBuilder.url(finalUrl).put(requestBody);
                    break;
                case "PATCH":
                    requestBuilder.url(finalUrl).patch(requestBody);
                    break;
                case "DELETE":
                    requestBuilder.url(finalUrl).delete(requestBody);
                    break;
                case "HEAD":
                    requestBuilder.url(finalUrl).head();
                    break;
                case "OPTIONS":
                    log.info("OPTIONS方法，切换到Hutool实现");
                    return sendUseHutoolWithMsg(httpMsg);
                default:
                    requestBuilder.url(finalUrl);
            }

            Request request = requestBuilder.build();

            log.info("HTTP请求构建完成, method: {}, url: {}", request.method(), request.url());

            log.debug("开始执行HTTP请求");
            response = okHttpClient.newCall(request).execute();
            log.info("HTTP请求执行完成, responseCode: {}, requestUrl: {}",
                    response.code(), request.url());

            // 读取响应体
            String responseBody = "";
            if (response.body() != null) {
                try {
                    responseBody = response.body().string();
                } catch (Exception e) {
                    log.warn("读取响应体失败: {}", e.getMessage());
                }
            }

            if (!response.isSuccessful()) {
                sendResult.setSuccess(false);
                sendResult.setInfo("HTTP请求失败，状态码: " + response.code() + ", 响应: " + responseBody);
                log.warn("HTTP请求失败, responseCode: {}, responseBody: {}", response.code(), responseBody);
                return sendResult;
            }
            sendResult.setInfo(responseBody);
            if (responseBody != null && responseBody.startsWith("{") && responseBody.endsWith("}")) {
                try {
                    responseBody = JSONUtil.toJsonPrettyStr(responseBody);
                } catch (Exception e) {
                    log.error("格式化JSON响应失败, error: {}", e.getMessage());
                }
            }
            sendResult.setBody(responseBody);

            sendResult.setHeaders(response.headers().toString());

            StringBuilder cookiesBuilder = StrUtil.builder();
            List<String> headerList = response.headers(Header.SET_COOKIE.toString());
            for (String cookieStr : headerList) {
                cookiesBuilder.append(cookieStr).append(StrUtil.CRLF);
            }

            sendResult.setCookies(cookiesBuilder.toString());

            sendResult.setSuccess(true);
            log.info("HTTP消息发送成功, responseCode: {}", response.code());
            return sendResult;
        } catch (Exception e) {
            log.error("HTTP消息发送异常, error: {}", e.getMessage());
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            return sendResult;
        } finally {
            // 确保响应被关闭，防止连接泄漏
            if (response != null) {
                try {
                    response.close();
                } catch (Exception e) {
                    log.warn("关闭响应时出错: {}", e.getMessage());
                }
            }
        }
    }

    public HttpSendResult sendUseOkHttp(String msgId) {
        log.info("开始使用OkHttp发送消息, msgId: {}", msgId);
        HttpSendResult sendResult = new HttpSendResult();
        Response response = null;
        try {
            log.debug("准备获取OkHttpClient, msgId: {}", msgId);
            OkHttpClient okHttpClient = getOkHttpClient();
            log.debug("OkHttpClient获取成功, msgId: {}", msgId);

            log.debug("准备构建HttpMsg, msgId: {}", msgId);
            HttpMsg httpMsg = httpMsgMaker.makeMsg(msgId);
            log.info("HttpMsg构建成功, msgId: {}, method: {}, url: {}, msgName: {}",
                    msgId, httpMsg.getMethod(), httpMsg.getUrl(), httpMsg.getMsgName());
            sendResult.setMsgName(httpMsg.getMsgName());

            return sendUseOkHttpWithMsg(httpMsg);

        } catch (Exception e) {
            log.error("HTTP消息发送异常, msgId: {}, error: {}",
                    msgId, e.getMessage());
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            return sendResult;
        }
    }

    private String cookieHeader(List<HttpCookie> cookies) {
        StringBuilder cookieHeader = new StringBuilder();
        for (int i = 0, size = cookies.size(); i < size; i++) {
            if (i > 0) {
                cookieHeader.append("; ");
            }
            HttpCookie cookie = cookies.get(i);
            cookieHeader.append(cookie.getName()).append('=').append(cookie.getValue());
        }
        return cookieHeader.toString();
    }

    private Proxy getProxy(Map<String, Object> configMap) {
        if (proxy == null) {
            synchronized (HttpMsgSender.class) {
                if (proxy == null) {
                    proxy = new Proxy(Proxy.Type.HTTP, new InetSocketAddress((String) configMap.get("host"), Integer.parseInt((String) configMap.get("port"))));
                }
            }
        }
        return proxy;
    }

    /**
     * 检查是否是本地请求
     */
    private boolean isLocalRequest(String url) {
        return url != null && (url.contains("localhost:") || url.contains("127.0.0.1:"));
    }

    public OkHttpClient getOkHttpClient() {
        log.debug("开始获取OkHttpClient");

        if (okHttpClient != null) {
            return okHttpClient;
        }

        try {
            MessageConfig messageConfig = messageConfigService.queryByMsgType(5);
            log.debug("MessageConfig查询成功, msgType: 5");

            if (messageConfig == null) {
                log.warn("未找到消息类型为5的配置，使用默认配置");
                return new OkHttpClient.Builder()
                        .connectTimeout(10, TimeUnit.SECONDS)  // 较短超时
                        .readTimeout(10, TimeUnit.SECONDS)
                        .writeTimeout(10, TimeUnit.SECONDS)
                        .build();
            }

            Map<String, Object> configMap = messageConfig.getConfigurationMap();
            log.debug("ConfigurationMap获取成功, configKeys: {}", configMap.keySet());

            synchronized (HttpMsgSender.class) {
                if (okHttpClient == null) {
                    log.debug("开始构建OkHttpClient");
                    OkHttpClient.Builder builder = new OkHttpClient.Builder()
                            .connectTimeout(10, TimeUnit.SECONDS)  // 较短超时，避免死锁
                            .readTimeout(10, TimeUnit.SECONDS)
                            .writeTimeout(10, TimeUnit.SECONDS);

                    boolean isHttpUseProxy = false;
                    if (configMap.containsKey("isHttpUseProxy")) {
                        Object proxyValue = configMap.get("isHttpUseProxy");
                        if (proxyValue instanceof Boolean) {
                            isHttpUseProxy = (Boolean) proxyValue;
                        } else if (proxyValue instanceof String) {
                            isHttpUseProxy = Boolean.parseBoolean((String) proxyValue);
                        }
                    }
                    log.debug("HTTP代理配置, isHttpUseProxy: {}", isHttpUseProxy);

                    if (isHttpUseProxy && configMap.containsKey("host") && configMap.containsKey("port")) {
                        String host = (String) configMap.get("host");
                        String portStr = (String) configMap.get("port");
                        try {
                            int port = Integer.parseInt(portStr);
                            Proxy proxy = new Proxy(Proxy.Type.HTTP, new InetSocketAddress(host, port));
                            builder.proxy(proxy);
                            log.debug("已设置HTTP代理: {}:{}", host, port);
                        } catch (NumberFormatException e) {
                            log.error("代理端口配置错误: {}", portStr);
                        }
                    }

                    // 使用较小的连接池
                    ConnectionPool pool = new ConnectionPool(5, 5, TimeUnit.MINUTES);
                    builder.connectionPool(pool);

                    okHttpClient = builder.build();
                    log.info("OkHttpClient构建成功");
                }
            }
        } catch (Exception e) {
            log.error("获取OkHttpClient失败, error: {}", e.getMessage(), e);
            // 返回默认客户端
            return new OkHttpClient.Builder()
                    .connectTimeout(10, TimeUnit.SECONDS)
                    .readTimeout(10, TimeUnit.SECONDS)
                    .writeTimeout(10, TimeUnit.SECONDS)
                    .build();
        }

        return okHttpClient;
    }
}