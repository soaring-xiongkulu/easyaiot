package com.basiclab.iot.infra.controller.admin.job.vo.job;

import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.basiclab.iot.infra.enums.DictTypeConstants;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

/**
 * JobRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 定时任务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class JobRespVO {

    @Schema(description = "任务编号", example = "1024")
    @ExcelProperty("任务编号")
    private Long id;

    @Schema(description = "任务名称", example = "测试任务")
    @ExcelProperty("任务名称")
    private String name;

    @Schema(description = "任务状态", example = "1")
    @ExcelProperty(value = "任务状态", converter = DictConvert.class)
    @DictFormat(DictTypeConstants.JOB_STATUS)
    private Integer status;

    @Schema(description = "处理器的名字", example = "sysUserSessionTimeoutJob")
    @ExcelProperty("处理器的名字")
    private String handlerName;

    @Schema(description = "处理器的参数", example = "Yudao")
    @ExcelProperty("处理器的参数")
    private String handlerParam;

    @Schema(description = "CRON 表达式", example = "0/10 * * * * ? *")
    @ExcelProperty("CRON 表达式")
    private String cronExpression;

    @Schema(description = "重试次数", example = "3")
    @NotNull(message = "重试次数不能为空")
    private Integer retryCount;

    @Schema(description = "重试间隔", example = "1000")
    private Integer retryInterval;

    @Schema(description = "监控超时时间", example = "1000")
    @ExcelProperty("监控超时时间")
    private Integer monitorTimeout;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}
