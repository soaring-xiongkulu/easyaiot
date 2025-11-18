package com.basiclab.iot.system.controller.admin.sms.vo.channel;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "管理后台 - 短信渠道精简 Response VO")
@Data
public class SmsChannelSimpleRespVO {

    @Schema(

/**
 * SmsChannelSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

description = "编号", example = "1024")
    private Long id;

    @Schema(description = "短信签名", example = "BasicLab源码")
    private String signature;

    @Schema(description = "渠道编码，参见 SmsChannelEnum 枚举类", example = "YUN_PIAN")
    private String code;

}
