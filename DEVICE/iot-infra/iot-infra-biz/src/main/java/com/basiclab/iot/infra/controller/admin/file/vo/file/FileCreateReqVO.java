package com.basiclab.iot.infra.controller.admin.file.vo.file;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

/**
 * FileCreateReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 文件创建 Request VO")
@Data
public class FileCreateReqVO {

    @NotNull(message = "文件配置编号不能为空")
    @Schema(description = "文件配置编号", example = "11")
    private Long configId;

    @NotNull(message = "文件路径不能为空")
    @Schema(description = "文件路径", example = "iot.jpg")
    private String path;

    @NotNull(message = "原文件名不能为空")
    @Schema(description = "原文件名", example = "iot.jpg")
    private String name;

    @NotNull(message = "文件 URL不能为空")
    @Schema(description = "文件 URL", example = "https://www.iocoder.cn/iot.jpg")
    private String url;

    @Schema(description = "文件 MIME 类型", example = "application/octet-stream")
    private String type;

    @Schema(description = "文件大小", example = "2048")
    private Integer size;

}
