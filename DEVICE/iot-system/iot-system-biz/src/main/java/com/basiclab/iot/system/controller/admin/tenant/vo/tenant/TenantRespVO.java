package com.basiclab.iot.system.controller.admin.tenant.vo.tenant;

import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.system.enums.DictTypeConstants;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * TenantRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 租户 Response VO")
@Data
@ExcelIgnoreUnannotated
public class TenantRespVO {

    @Schema(description = "租户编号", example = "1024")
    @ExcelProperty("租户编号")
    private Long id;

    @Schema(description = "租户名", example = "BasicLab")
    @ExcelProperty("租户名")
    private String name;

    @Schema(description = "联系人", example = "BasicLab")
    @ExcelProperty("联系人")
    private String contactName;

    @Schema(description = "联系手机", example = "15601691300")
    @ExcelProperty("联系手机")
    private String contactMobile;

    @Schema(description = "租户状态", example = "1")
    @ExcelProperty(value = "状态", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.COMMON_STATUS)
    private Integer status;

    @Schema(description = "绑定域名", example = "https://www.iocoder.cn")
    private String website;

    @Schema(description = "租户套餐编号", example = "1024")
    private Long packageId;

    @Schema(description = "过期时间")
    private LocalDateTime expireTime;

    @Schema(description = "账号数量", example = "1024")
    private Integer accountCount;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}
