package com.basiclab.iot.system.controller.admin.notify.vo.template;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * NotifyTemplateRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 站内信模版 Response VO")
@Data
public class NotifyTemplateRespVO {

    @Schema(description = "ID", example = "1024")
    private Long id;

    @Schema(description = "模版名称", example = "测试模版")
    private String name;

    @Schema(description = "模版编码", example = "SEND_TEST")
    private String code;

    @Schema(description = "模版类型，对应 system_notify_template_type 字典", example = "1")
    private Integer type;

    @Schema(description = "发送人名称", example = "土豆")
    private String nickname;

    @Schema(description = "模版内容", example = "我是模版内容")
    private String content;

    @Schema(description = "参数数组", example = "name,code")
    private List<String> params;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举", example = "1")
    private Integer status;

    @Schema(description = "备注", example = "我是备注")
    private String remark;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
