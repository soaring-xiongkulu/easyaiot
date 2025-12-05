package com.basiclab.iot.system.api.notify.dto;

import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * NotifyTemplateRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class NotifyTemplateRespDTO implements Serializable {

    /**
     * ID
     */
    private Long id;

    /**
     * 模版名称
     */
    private String name;

    /**
     * 模版编码
     */
    private String code;

    /**
     * 模版类型
     */
    private Integer type;

    /**
     * 发送人名称
     */
    private String nickname;

    /**
     * 模版内容
     */
    private String content;

    /**
     * 参数数组
     */
    private List<String> params;

    /**
     * 状态
     */
    private Integer status;

    /**
     * 备注
     */
    private String remark;
}

