package com.basiclab.iot.device.controller.webhook;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.device.domain.model.dto.WebhookTestDto;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Map;

/**
 * Webhook测试推送Controller
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-12-04
 */
@Slf4j
@RestController
@RequestMapping("/device/webhook/test")
@Tag(name = "Webhook测试推送")
public class WebhookTestController {

    /**
     * 初始化日志，确认Controller是否被加载
     */
    @javax.annotation.PostConstruct
    public void init() {
        log.info("========== WebhookTestController 已初始化 ==========");
        log.info("Controller路径映射: /device/webhook/test");
        log.info("testParams端点: POST /device/webhook/test/testParams");
        log.info("testBody端点: POST /device/webhook/test/testBody");
    }

    /**
     * Webhook测试推送 - Params方式（URL参数）
     *
     * @param webhookUrl Webhook地址
     * @param testParam1 测试参数1
     * @param testParam2 测试参数2
     * @param request HTTP请求对象
     * @return 测试结果
     */
    @PostMapping("/testParams")
    @ApiOperation("Webhook测试推送 - Params方式（URL参数）")
    public AjaxResult testWebhookParams(
            @RequestParam(required = false) String webhookUrl,
            @RequestParam(required = false) String testParam1,
            @RequestParam(required = false) String testParam2,
            HttpServletRequest request) {
        
        log.info("========== Webhook测试推送 - Params方式 ==========");
        log.info("✅ 请求已到达 WebhookTestController.testWebhookParams 方法");
        log.info("请求URI: {}", request.getRequestURI());
        log.info("请求URL: {}", request.getRequestURL());
        log.info("请求方法: {}", request.getMethod());
        log.info("上下文路径: {}", request.getContextPath());
        log.info("Servlet路径: {}", request.getServletPath());
        log.info("路径信息: {}", request.getPathInfo());
        
        // 解析并打印请求头
        Map<String, String> headers = parseHeaders(request);
        log.info("接收到的请求头信息：");
        headers.forEach((key, value) -> log.info("  {}: {}", key, value));
        
        // 打印接收到的参数
        log.info("接收到的URL参数：");
        log.info("  webhookUrl: {}", webhookUrl);
        log.info("  testParam1: {}", testParam1);
        log.info("  testParam2: {}", testParam2);
        
        // 构建返回结果
        Map<String, Object> result = new HashMap<>();
        result.put("webhookUrl", webhookUrl);
        result.put("testParam1", testParam1);
        result.put("testParam2", testParam2);
        result.put("headers", headers);
        result.put("method", "Params方式（URL参数）");
        
        // 打印测试成功信息
        String successMessage = String.format(
            "✅ Webhook测试推送成功！\n" +
            "   测试方式: Params方式（URL参数）\n" +
            "   Webhook地址: %s\n" +
            "   测试参数1: %s\n" +
            "   测试参数2: %s\n" +
            "   请求头数量: %d\n" +
            "   测试时间: %s",
            webhookUrl != null ? webhookUrl : "未提供",
            testParam1 != null ? testParam1 : "未提供",
            testParam2 != null ? testParam2 : "未提供",
            headers.size(),
            java.time.LocalDateTime.now()
        );
        log.info(successMessage);
        
        return AjaxResult.success("Webhook测试推送成功 - Params方式", result);
    }

    /**
     * Webhook测试推送 - 简单GET测试
     *
     * @return 测试结果
     */
    @GetMapping("/test")
    @ApiOperation("Webhook测试推送 - 简单GET测试")
    public AjaxResult testWebhook() {
        log.info("========== Webhook测试推送 - GET测试 ==========");
        log.info("✅ 请求已到达 WebhookTestController.testWebhook 方法");
        Map<String, Object> result = new HashMap<>();
        result.put("message", "Webhook Controller 已正常工作");
        return AjaxResult.success("Webhook测试推送成功 - GET测试", result);
    }

    /**
     * Webhook测试推送 - Body方式（请求体）
     *
     * @param webhookTestDto 测试数据DTO
     * @param request HTTP请求对象
     * @return 测试结果
     */
    @PostMapping("/testBody")
    @ApiOperation("Webhook测试推送 - Body方式（请求体）")
    public AjaxResult testWebhookBody(
            @RequestBody(required = false) WebhookTestDto webhookTestDto,
            HttpServletRequest request) {
        
        log.info("========== Webhook测试推送 - Body方式 ==========");
        log.info("✅ 请求已到达 WebhookTestController.testWebhookBody 方法");
        log.info("请求URI: {}", request.getRequestURI());
        log.info("请求URL: {}", request.getRequestURL());
        log.info("请求方法: {}", request.getMethod());
        log.info("上下文路径: {}", request.getContextPath());
        log.info("Servlet路径: {}", request.getServletPath());
        log.info("路径信息: {}", request.getPathInfo());
        
        // 解析并打印请求头
        Map<String, String> headers = parseHeaders(request);
        log.info("接收到的请求头信息：");
        headers.forEach((key, value) -> log.info("  {}: {}", key, value));
        
        // 如果DTO为空，创建一个默认的
        if (webhookTestDto == null) {
            webhookTestDto = new WebhookTestDto();
        }
        
        // 打印接收到的Body数据
        log.info("接收到的请求体数据：");
        log.info("  webhookUrl: {}", webhookTestDto.getWebhookUrl());
        log.info("  testParam1: {}", webhookTestDto.getTestParam1());
        log.info("  testParam2: {}", webhookTestDto.getTestParam2());
        log.info("  testData: {}", webhookTestDto.getTestData());
        
        // 构建返回结果
        Map<String, Object> result = new HashMap<>();
        result.put("webhookUrl", webhookTestDto.getWebhookUrl());
        result.put("testParam1", webhookTestDto.getTestParam1());
        result.put("testParam2", webhookTestDto.getTestParam2());
        result.put("testData", webhookTestDto.getTestData());
        result.put("headers", headers);
        result.put("method", "Body方式（请求体）");
        
        // 打印测试成功信息
        String successMessage = String.format(
            "✅ Webhook测试推送成功！\n" +
            "   测试方式: Body方式（请求体）\n" +
            "   Webhook地址: %s\n" +
            "   测试参数1: %s\n" +
            "   测试参数2: %s\n" +
            "   测试数据: %s\n" +
            "   请求头数量: %d\n" +
            "   测试时间: %s",
            webhookTestDto.getWebhookUrl() != null ? webhookTestDto.getWebhookUrl() : "未提供",
            webhookTestDto.getTestParam1() != null ? webhookTestDto.getTestParam1() : "未提供",
            webhookTestDto.getTestParam2() != null ? webhookTestDto.getTestParam2() : "未提供",
            webhookTestDto.getTestData() != null ? webhookTestDto.getTestData() : "未提供",
            headers.size(),
            java.time.LocalDateTime.now()
        );
        log.info(successMessage);
        
        return AjaxResult.success("Webhook测试推送成功 - Body方式", result);
    }

    /**
     * 解析HTTP请求头
     *
     * @param request HTTP请求对象
     * @return 请求头Map
     */
    private Map<String, String> parseHeaders(HttpServletRequest request) {
        Map<String, String> headers = new HashMap<>();
        Enumeration<String> headerNames = request.getHeaderNames();
        
        if (headerNames != null) {
            while (headerNames.hasMoreElements()) {
                String headerName = headerNames.nextElement();
                String headerValue = request.getHeader(headerName);
                headers.put(headerName, headerValue);
            }
        }
        
        return headers;
    }
}

