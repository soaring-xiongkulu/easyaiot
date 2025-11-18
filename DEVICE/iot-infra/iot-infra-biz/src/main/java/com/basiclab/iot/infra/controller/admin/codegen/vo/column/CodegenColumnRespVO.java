package com.basiclab.iot.infra.controller.admin.codegen.vo.column;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * CodegenColumnRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 代码生成字段定义 Response VO")
@Data
public class CodegenColumnRespVO {

    @Schema(description = "编号", example = "1")
    private Long id;

    @Schema(description = "表编号", example = "1")
    private Long tableId;

    @Schema(description = "字段名", example = "user_age")
    private String columnName;

    @Schema(description = "字段类型", example = "int(11)")
    private String dataType;

    @Schema(description = "字段描述", example = "年龄")
    private String columnComment;

    @Schema(description = "是否允许为空", example = "true")
    private Boolean nullable;

    @Schema(description = "是否主键", example = "false")
    private Boolean primaryKey;

    @Schema(description = "排序", example = "10")
    private Integer ordinalPosition;

    @Schema(description = "Java 属性类型", example = "userAge")
    private String javaType;

    @Schema(description = "Java 属性名", example = "Integer")
    private String javaField;

    @Schema(description = "字典类型", example = "sys_gender")
    private String dictType;

    @Schema(description = "数据示例", example = "1024")
    private String example;

    @Schema(description = "是否为 Create 创建操作的字段", example = "true")
    private Boolean createOperation;

    @Schema(description = "是否为 Update 更新操作的字段", example = "false")
    private Boolean updateOperation;

    @Schema(description = "是否为 List 查询操作的字段", example = "true")
    private Boolean listOperation;

    @Schema(description = "List 查询操作的条件类型，参见 CodegenColumnListConditionEnum 枚举", example = "LIKE")
    private String listOperationCondition;

    @Schema(description = "是否为 List 查询操作的返回字段", example = "true")
    private Boolean listOperationResult;

    @Schema(description = "显示类型", example = "input")
    private String htmlType;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
