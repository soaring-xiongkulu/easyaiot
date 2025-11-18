package com.basiclab.iot.system.controller.admin.sms.vo.template;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

/**
 * SmsTemplateSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 短信模板创建/修改 Request VO")
@Data
public class SmsTemplateSaveReqVO {

    @Schema(description = "编号", example = "1024")
    private Long id;

    @Schema(description = "短信类型，参见 SmsTemplateTypeEnum 枚举类", example = "1")
    @NotNull(message = "短信类型不能为空")
    private Integer type;

    @Schema(description = "开启状态，参见 CommonStatusEnum 枚举类", example = "1")
    @NotNull(message = "开启状态不能为空")
    private Integer status;

    @Schema(description = "模板编码", example = "test_01")
    @NotNull(message = "模板编码不能为空")
    private String code;

    @Schema(description = "模板名称", example = "Yudao")
    @NotNull(message = "模板名称不能为空")
    private String name;

    @Schema(description = "模板内容", example = "你好，{name}。你长的太{like}啦！")
    @NotNull(message = "模板内容不能为空")
    private String content;

    @Schema(description = "备注", example = "哈哈哈")
    private String remark;

    @Schema(description = "短信 API 的模板编号", example = "4383920")
    @NotNull(message = "短信 API 的模板编号不能为空")
    private String apiTemplateId;

    @Schema(description = "短信渠道编号", example = "10")
    @NotNull(message = "短信渠道编号不能为空")
    private Long channelId;

}
