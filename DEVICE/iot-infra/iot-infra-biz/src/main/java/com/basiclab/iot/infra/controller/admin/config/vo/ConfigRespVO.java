package com.basiclab.iot.infra.controller.admin.config.vo;

import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.infra.enums.DictTypeConstants;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * ConfigRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 参数配置信息 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ConfigRespVO {

    @Schema(description = "参数配置序号", example = "1024")
    @ExcelProperty("参数配置序号")
    private Long id;

    @Schema(description = "参数分类", example = "biz")
    @ExcelProperty("参数分类")
    private String category;

    @Schema(description = "参数名称", example = "数据库名")
    @ExcelProperty("参数名称")
    private String name;

    @Schema(description = "参数键名", example = "yunai.db.username")
    @ExcelProperty("参数键名")
    private String key;

    @Schema(description = "参数键值", example = "1024")
    @ExcelProperty("参数键值")
    private String value;

    @Schema(description = "参数类型，参见 SysConfigTypeEnum 枚举", example = "1")
    @ExcelProperty(value = "参数类型", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.CONFIG_TYPE)
    private Integer type;

    @Schema(description = "是否可见", example = "true")
    @ExcelProperty(value = "是否可见", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.BOOLEAN_STRING)
    private Boolean visible;

    @Schema(description = "备注", example = "备注一下很帅气！")
    @ExcelProperty("备注")
    private String remark;

    @Schema(description = "创建时间", example = "时间戳格式")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}
