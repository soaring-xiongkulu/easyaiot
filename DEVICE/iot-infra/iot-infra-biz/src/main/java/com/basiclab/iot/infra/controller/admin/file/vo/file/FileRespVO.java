package com.basiclab.iot.infra.controller.admin.file.vo.file;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * FileRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 文件 Response VO,不返回 content 字段，太大")
@Data
public class FileRespVO {

    @Schema(description = "文件编号", example = "1024")
    private Long id;

    @Schema(description = "配置编号", example = "11")
    private Long configId;

    @Schema(description = "文件路径", example = "iot.jpg")
    private String path;

    @Schema(description = "原文件名", example = "iot.jpg")
    private String name;

    @Schema(description = "文件 URL", example = "https://www.iocoder.cn/iot.jpg")
    private String url;

    @Schema(description = "文件MIME类型", example = "application/octet-stream")
    private String type;

    @Schema(description = "文件大小", example = "2048")
    private Integer size;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
