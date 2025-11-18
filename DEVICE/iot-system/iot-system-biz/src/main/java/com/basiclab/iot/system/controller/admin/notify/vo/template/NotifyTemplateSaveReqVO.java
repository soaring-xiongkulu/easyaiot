package com.basiclab.iot.system.controller.admin.notify.vo.template;

import com.basiclab.iot.common.enums.CommonStatusEnum;
import com.basiclab.iot.common.validation.InEnum;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

/**
 * NotifyTemplateSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 站内信模版创建/修改 Request VO")
@Data
public class NotifyTemplateSaveReqVO {

    @Schema(description = "ID", example = "1024")
    private Long id;

    @Schema(description = "模版名称", example = "测试模版")
    @NotEmpty(message = "模版名称不能为空")
    private String name;

    @Schema(description = "模版编码", example = "SEND_TEST")
    @NotNull(message = "模版编码不能为空")
    private String code;

    @Schema(description = "模版类型，对应 system_notify_template_type 字典", example = "1")
    @NotNull(message = "模版类型不能为空")
    private Integer type;

    @Schema(description = "发送人名称", example = "土豆")
    @NotEmpty(message = "发送人名称不能为空")
    private String nickname;

    @Schema(description = "模版内容", example = "我是模版内容")
    @NotEmpty(message = "模版内容不能为空")
    private String content;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举", example = "1")
    @NotNull(message = "状态不能为空")
    @InEnum(value = CommonStatusEnum.class, message = "状态必须是 {value}")
    private Integer status;

    @Schema(description = "备注", example = "我是备注")
    private String remark;

}
