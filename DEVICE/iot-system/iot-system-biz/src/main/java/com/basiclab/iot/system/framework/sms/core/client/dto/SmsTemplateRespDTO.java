package com.basiclab.iot.system.framework.sms.core.client.dto;

import com.basiclab.iot.system.framework.sms.core.enums.SmsTemplateAuditStatusEnum;
import lombok.Data;

/**
 * 短信模板 Response DTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class SmsTemplateRespDTO {

    /**
     * 模板编号
     */
    private String id;
    /**
     * 短信内容
     */
    private String content;
    /**
     * 审核状态
     *
     * 枚举 {@link SmsTemplateAuditStatusEnum}
     */
    private Integer auditStatus;
    /**
     * 审核未通过的理由
     */
    private String auditReason;

}
