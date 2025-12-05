package com.basiclab.iot.system.api.mail.dto;

import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * MailTemplateRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class MailTemplateRespDTO implements Serializable {

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
     * 发送的邮箱账号编号
     */
    private Long accountId;

    /**
     * 发送人名称
     */
    private String nickname;

    /**
     * 标题
     */
    private String title;

    /**
     * 内容
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

