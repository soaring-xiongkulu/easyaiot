package com.basiclab.iot.system.controller.admin.notify.vo.message;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * NotifyMessageRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 站内信 Response VO")
@Data
public class NotifyMessageRespVO {

    @Schema(description = "ID", example = "1024")
    private Long id;

    @Schema(description = "用户编号", example = "25025")
    private Long userId;

    @Schema(description = "用户类型，参见 UserTypeEnum 枚举", example = "1")
    private Byte userType;

    @Schema(description = "模版编号", example = "13013")
    private Long templateId;

    @Schema(description = "模板编码", example = "test_01")
    private String templateCode;

    @Schema(description = "模版发送人名称", example = "BasicLab")
    private String templateNickname;

    @Schema(description = "模版内容", example = "测试内容")
    private String templateContent;

    @Schema(description = "模版类型", example = "2")
    private Integer templateType;

    @Schema(description = "模版参数")
    private Map<String, Object> templateParams;

    @Schema(description = "是否已读", example = "true")
    private Boolean readStatus;

    @Schema(description = "阅读时间")
    private LocalDateTime readTime;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
