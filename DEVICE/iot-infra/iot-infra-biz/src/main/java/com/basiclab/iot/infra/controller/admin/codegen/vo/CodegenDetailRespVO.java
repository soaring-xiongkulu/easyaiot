package com.basiclab.iot.infra.controller.admin.codegen.vo;

import com.basiclab.iot.infra.controller.admin.codegen.vo.column.CodegenColumnRespVO;
import com.basiclab.iot.infra.controller.admin.codegen.vo.table.CodegenTableRespVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

/**
 * CodegenDetailRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 代码生成表和字段的明细 Response VO")
@Data
public class CodegenDetailRespVO {

    @Schema(description = "表定义")
    private CodegenTableRespVO table;

    @Schema(description = "字段定义")
    private List<CodegenColumnRespVO> columns;

}
