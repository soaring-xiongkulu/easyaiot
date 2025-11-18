package com.basiclab.iot.system.controller.admin.permission.vo.role;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.system.enums.DictTypeConstants;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import java.time.LocalDateTime;
import java.util.Set;

/**
 * RoleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 角色信息 Response VO")
@Data
@ExcelIgnoreUnannotated
public class RoleRespVO {

    @Schema(description = "角色编号", example = "1")
    @ExcelProperty("角色序号")
    private Long id;

    @Schema(description = "角色名称", example = "管理员")
    @ExcelProperty("角色名称")
    private String name;

    @Schema(description = "角色标志", example = "admin")
    @NotBlank(message = "角色标志不能为空")
    @ExcelProperty("角色标志")
    private String code;

    @Schema(description = "显示顺序", example = "1024")
    @ExcelProperty("角色排序")
    private Integer sort;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举类", example = "1")
    @ExcelProperty(value = "角色状态", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.COMMON_STATUS)
    private Integer status;

    @Schema(description = "角色类型，参见 RoleTypeEnum 枚举类", example = "1")
    private Integer type;

    @Schema(description = "备注", example = "我是一个角色")
    private String remark;

    @Schema(description = "数据范围，参见 DataScopeEnum 枚举类", example = "1")
    @ExcelProperty("数据范围")
    private Integer dataScope;

    @Schema(description = "数据范围(指定部门数组)", example = "1")
    private Set<Long> dataScopeDeptIds;

    @Schema(description = "创建时间", example = "时间戳格式")
    private LocalDateTime createTime;

}
