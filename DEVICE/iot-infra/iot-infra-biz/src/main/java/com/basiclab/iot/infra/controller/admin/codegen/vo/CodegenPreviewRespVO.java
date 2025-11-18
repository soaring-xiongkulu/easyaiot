package com.basiclab.iot.infra.controller.admin.codegen.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * CodegenPreviewRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 代码生成预览 Response VO，注意，每个文件都是一个该对象")
@Data
public class CodegenPreviewRespVO {

    @Schema(description = "文件路径", example = "java/cn/iocoder/Yudao/adminserver/modules/system/controller/test/SysTestDemoController.java")
    private String filePath;

    @Schema(description = "代码", example = "Hello World")
    private String code;

}
