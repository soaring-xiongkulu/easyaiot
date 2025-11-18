package com.basiclab.iot.system.controller.admin.sms.vo.channel;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import org.hibernate.validator.constraints.URL;

import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

/**
 * SmsChannelRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管
理后台 - 短信渠道 Response VO")
@Data
public class SmsChannelRespVO {

    @Schema(description = "编号", example = "1024")
    private Long id;

    @Schema(description = "短信签名", example = "BasicLab源码")
    @NotNull(message = "短信签名不能为空")
    private String signature;

    @Schema(description = "渠道编码，参见 SmsChannelEnum 枚举类", example = "YUN_PIAN")
    private String code;

    @Schema(description = "启用状态", example = "1")
    @NotNull(message = "启用状态不能为空")
    private Integer status;

    @Schema(description = "备注", example = "好吃！")
    private String remark;

    @Schema(description = "短信 API 的账号", example = "Yudao")
    @NotNull(message = "短信 API 的账号不能为空")
    private String apiKey;

    @Schema(description = "短信 API 的密钥", example = "yuanma")
    private String apiSecret;

    @Schema(description = "短信发送回调 URL", example = "https://www.iocoder.cn")
    @URL(message = "回调 URL 格式不正确")
    private String callbackUrl;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
