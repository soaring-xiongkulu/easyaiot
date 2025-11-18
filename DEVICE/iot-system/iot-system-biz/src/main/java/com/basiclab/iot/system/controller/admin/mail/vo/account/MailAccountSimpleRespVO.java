package com.basiclab.iot.system.controller.admin.mail.vo.account;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * MailAccountSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 邮箱账号的精简 Response VO")
@Data
public class MailAccountSimpleRespVO {

    @Schema(description = "邮箱编号", example = "1024")
    private Long id;

    @Schema(description = "邮箱", example = "768541388@qq.com")
    private String mail;

}
