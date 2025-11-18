package com.basiclab.iot.infra.api.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;

/**
 * FileCreateReqDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 文件创建 Request DTO")
@Data
public class FileCreateReqDTO {

    @Schema(description = "原文件名称", example = "xxx.png")
    private String name;

    @Schema(description = "文件路径", example = "xxx.png")
    private String path;

    @Schema(description = "文件内容")
    @NotEmpty(message = "文件内容不能为空")
    private byte[] content;

}
