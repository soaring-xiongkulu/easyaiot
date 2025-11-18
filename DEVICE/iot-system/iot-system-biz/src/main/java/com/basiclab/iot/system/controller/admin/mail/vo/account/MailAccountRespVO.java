package com.basiclab.iot.system.controller.admin.mail.vo.account;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * MailAccountRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 邮箱账号 Response VO")
@Data
public class MailAccountRespVO {

    @Schema(description = "编号", example = "1024")
    private Long id;

    @Schema(description = "邮箱", example = "Yudaoyuanma@123.com")
    private String mail;

    @Schema(description = "用户名", example = "Yudao")
    private String username;

    @Schema(description = "密码", example = "123456")
    private String password;

    @Schema(description = "SMTP 服务器域名", example = "www.iocoder.cn")
    private String host;

    @Schema(description = "SMTP 服务器端口", example = "80")
    private Integer port;

    @Schema(description = "是否开启 ssl", example = "true")
    private Boolean sslEnable;

    @Schema(description = "是否开启 starttls", example = "true")
    private Boolean starttlsEnable;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
