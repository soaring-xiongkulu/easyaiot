package com.basiclab.iot.system.controller.admin.mail.vo.template;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * MailTemplateSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 邮件模版的精简 Response VO")
@Data
public class MailTemplateSimpleRespVO {

    @Schema(description = "模版编号", example = "1024")
    private Long id;

    @Schema(description = "模版名字", example = "哒哒哒")
    private String name;

}
