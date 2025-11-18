package com.basiclab.iot.system.controller.admin.mail.vo.account;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;

/**
 * MailAccountSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 邮箱账号创建/修改 Request VO")
@Data
public class MailAccountSaveReqVO {

    @Schema(description = "编号", example = "1024")
    private Long id;

    @Schema(description = "邮箱", example = "Yudaoyuanma@123.com")
    @NotNull(message = "邮箱不能为空")
    @Email(message = "必须是 Email 格式")
    private String mail;

    @Schema(description = "用户名", example = "Yudao")
    @NotNull(message = "用户名不能为空")
    private String username;

    @Schema(description = "密码", example = "123456")
    @NotNull(message = "密码必填")
    private String password;

    @Schema(description = "SMTP 服务器域名", example = "www.iocoder.cn")
    @NotNull(message = "SMTP 服务器域名不能为空")
    private String host;

    @Schema(description = "SMTP 服务器端口", example = "80")
    @NotNull(message = "SMTP 服务器端口不能为空")
    private Integer port;

    @Schema(description = "是否开启 ssl", example = "true")
    @NotNull(message = "是否开启 ssl 必填")
    private Boolean sslEnable;

    @Schema(description = "是否开启 starttls", example = "true")
    @NotNull(message = "是否开启 starttls 必填")
    private Boolean starttlsEnable;

}
