/**
  * Copyright 2021 json.cn 
  */
package com.basiclab.iot.device.domain.product.model;
import lombok.Data;

import java.util.List;

/**
 * 产品模型服务命令对象 Commands
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2024-12-23
 */
@Data
public class Commands {
    private static final long serialVersionUID = 1L;
    private String name;
    private String description;
    private List<Properties> requests;
    private List<Properties> responses;

}