package com.basiclab.iot.system.controller.admin.logger.vo.loginlog;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.system.enums.DictTypeConstants;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * LoginLogRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 登录日志 Response VO")
@Data
@ExcelIgnoreUnannotated
public class LoginLogRespVO {

    @Schema(description = "日志编号", example = "1024")
    @ExcelProperty("日志主键")
    private Long id;

    @Schema(description = "日志类型，参见 LoginLogTypeEnum 枚举类", example = "1")
    @ExcelProperty(value = "日志类型", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.LOGIN_TYPE)
    private Integer logType;

    @Schema(description = "用户编号", example = "666")
    private Long userId;

    @Schema(description = "用户类型，参见 UserTypeEnum 枚举", example = "2")
    private Integer userType;

    @Schema(description = "链路追踪编号", example = "89aca178-a370-411c-ae02-3f0d672be4ab")
    private String traceId;

    @Schema(description = "用户账号", example = "Yudao")
    @ExcelProperty("用户账号")
    private String username;

    @Schema(description = "登录结果，参见 LoginResultEnum 枚举类", example = "1")
    @ExcelProperty(value = "登录结果", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.LOGIN_RESULT)
    private Integer result;

    @Schema(description = "用户 IP", example = "127.0.0.1")
    @ExcelProperty("登录 IP")
    private String userIp;

    @Schema(description = "浏览器 UserAgent", example = "Mozilla/5.0")
    @ExcelProperty("浏览器 UA")
    private String userAgent;

    @Schema(description = "登录时间")
    @ExcelProperty("登录时间")
    private LocalDateTime createTime;

}
