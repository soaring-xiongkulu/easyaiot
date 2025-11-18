package com.basiclab.iot.infra.controller.admin.codegen.vo.table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "管理后台 - 数据库的表定义 Response VO")
@Data
public class DatabaseTableRespVO {

    @Schema

/**
 * DatabaseTableRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

(description = "表名称", example = "yuanma")
    private String name;

    @Schema(description = "表描述", example = "BasicLab源码")
    private String comment;

}
