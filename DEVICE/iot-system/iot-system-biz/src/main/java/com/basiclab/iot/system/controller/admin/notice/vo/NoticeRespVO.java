package com.basiclab.iot.system.controller.admin.notice.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * NoticeRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 通知公告信息 Response VO")
@Data
public class NoticeRespVO {

    @Schema(description = "通知公告序号", example = "1024")
    private Long id;

    @Schema(description = "公告标题", example = "小博主")
    private String title;

    @Schema(description = "公告类型", example = "小博主")
    private Integer type;

    @Schema(description = "公告内容", example = "半生编码")
    private String content;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举类", example = "1")
    private Integer status;

    @Schema(description = "创建时间", example = "时间戳格式")
    private LocalDateTime createTime;

}
