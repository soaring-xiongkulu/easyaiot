package com.basiclab.iot.system.controller.admin.mail.vo.template;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * MailTemplateRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 邮件末班 Response VO")
@Data
public class MailTemplateRespVO {

    @Schema(description = "编号", example = "1024")
    private Long id;

    @Schema(description = "模版名称", example = "测试名字")
    private String name;

    @Schema(description = "模版编号", example = "test")
    private String code;

    @Schema(description = "发送的邮箱账号编号", example = "1")
    private Long accountId;

    @Schema(description = "发送人名称", example = "芋头")
    private String nickname;

    @Schema(description = "标题", example = "注册成功")
    private String title;

    @Schema(description = "内容", example = "你好，注册成功啦")
    private String content;

    @Schema(description = "参数数组", example = "name,code")
    private List<String> params;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举", example = "1")
    private Integer status;

    @Schema(description = "备注", example = "奥特曼")
    private String remark;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
