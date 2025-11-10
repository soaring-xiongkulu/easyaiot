/**
  * Copyright 2021 json.cn
  */
package com.basiclab.iot.device.domain.product.model;
import lombok.Data;

import java.util.List;

/**
 * 产品模型服务能力描述对象 Services
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2024-12-23
 */
@Data
public class Services{
    private static final long serialVersionUID = 1L;
    private Long productId;
    private String serviceId;
    private String serviceCode;
    private String serviceName;
    private String description;
    private List<Commands> commands;
    private List<Properties> properties;
}
