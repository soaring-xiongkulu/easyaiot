package com.basiclab.iot.system.controller.admin.sms.vo.channel;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import org.hibernate.validator.constraints.URL;

import javax.validation.constraints.NotNull;

@Schema(description = "管理后台 - 短信渠道创建/修改 Request VO")
@Data

/**
 * SmsChannelSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class SmsChannelSaveReqVO {

    @Schema(description = "编号", example = "1024")
    private Long id;

    @Schema(description = "短信签名", example = "BasicLab源码")
    @NotNull(message = "短信签名不能为空")
    private String signature;

    @Schema(description = "渠道编码，参见 SmsChannelEnum 枚举类", example = "YUN_PIAN")
    @NotNull(message = "渠道编码不能为空")
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

    @Schema(description = "短信发送回调 URL", example = "https://github.com/soaring-xiongkulu/easyaiot")
    @URL(message = "回调 URL 格式不正确")
    private String callbackUrl;

}
