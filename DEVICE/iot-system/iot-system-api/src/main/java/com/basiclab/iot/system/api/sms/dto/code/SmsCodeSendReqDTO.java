package com.basiclab.iot.system.api.sms.dto.code;

import com.basiclab.iot.common.validation.InEnum;
import com.basiclab.iot.common.validation.Mobile;
import com.basiclab.iot.system.enums.sms.SmsSceneEnum;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

/**
 * SmsCodeSendReqDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 短信验证码的发送 Request DTO")
@Data
public class SmsCodeSendReqDTO {

    @Schema(description = "手机号", example = "15601691300")
    @Mobile
    @NotEmpty(message = "手机号不能为空")
    private String mobile;

    @Schema(description = "发送场景", example = "1")
    @NotNull(message = "发送场景不能为空")
    @InEnum(SmsSceneEnum.class)

    private Integer scene;
    @Schema(description = "发送 IP", example = "10.20.30.40")
    @NotEmpty(message = "发送 IP 不能为空")
    private String createIp;

}
