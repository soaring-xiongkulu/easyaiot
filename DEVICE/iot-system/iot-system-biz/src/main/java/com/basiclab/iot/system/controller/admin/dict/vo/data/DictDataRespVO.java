package com.basiclab.iot.system.controller.admin.dict.vo.data;

import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.system.enums.DictTypeConstants;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * DictDataRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 字典数据信息 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DictDataRespVO {

    @Schema(description = "字典数据编号", example = "1024")
    @ExcelProperty("字典编码")
    private Long id;

    @Schema(description = "显示顺序", example = "1024")
    @ExcelProperty("字典排序")
    private Integer sort;

    @Schema(description = "字典标签", example = "BasicLab")
    @ExcelProperty("字典标签")
    private String label;

    @Schema(description = "字典值", example = "iocoder")
    @ExcelProperty("字典键值")
    private String value;

    @Schema(description = "字典类型", example = "sys_common_sex")
    @ExcelProperty("字典类型")
    private String dictType;

    @Schema(description = "状态,见 CommonStatusEnum 枚举", example = "1")
    @ExcelProperty(value = "状态", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.COMMON_STATUS)
    private Integer status;

    @Schema(description = "颜色类型,default、primary、success、info、warning、danger", example = "default")
    private String colorType;

    @Schema(description = "css 样式", example = "btn-visible")
    private String cssClass;

    @Schema(description = "备注", example = "我是一个角色")
    private String remark;

    @Schema(description = "创建时间", example = "时间戳格式")
    private LocalDateTime createTime;

}
