package com.basiclab.iot.system.api.mail.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;
import java.util.Map;

/**
 * MailSendSingleToUserReqDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 邮件发送给 Admin 或者 Member 用户 Request DTO")
@Data
public class MailSendSingleToUserReqDTO {

    @Schema(description = "用户编号", example = "1024")
    private Long userId;
    @Schema(description = "手机号", example = "15601691300")
    @Email
    private String mail;

    @Schema(description = "邮件模板编号", example = "USER_SEND")
    @NotNull(message = "邮件模板编号不能为空")
    private String templateCode;

    @Schema(description = "邮件模板参数")
    private Map<String, Object> templateParams;

}
