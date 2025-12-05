package com.basiclab.iot.device.domain.model.dto;

import lombok.Data;

/**
 * Webhook测试DTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-12-04
 */
@Data
public class WebhookTestDto {
    
    /**
     * Webhook地址
     */
    private String webhookUrl;
    
    /**
     * 测试参数1
     */
    private String testParam1;
    
    /**
     * 测试参数2
     */
    private String testParam2;
    
    /**
     * 测试数据（可以是JSON字符串或其他格式）
     */
    private String testData;
}

