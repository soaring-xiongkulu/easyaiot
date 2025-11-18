package com.basiclab.iot.infra.controller.admin.job.vo.job;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

/**
 * JobSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Schema(description = "管理后台 - 定时任务创建/修改 Request VO")
@Data
public class JobSaveReqVO {

    @Schema(description = "任务编号", example = "1024")
    private Long id;

    @Schema(description = "任务名称", example = "测试任务")
    @NotEmpty(message = "任务名称不能为空")
    private String name;

    @Schema(description = "处理器的名字", example = "sysUserSessionTimeoutJob")
    @NotEmpty(message = "处理器的名字不能为空")
    private String handlerName;

    @Schema(description = "处理器的参数", example = "Yudao")
    private String handlerParam;

    @Schema(description = "CRON 表达式", example = "0/10 * * * * ? *")
    @NotEmpty(message = "CRON 表达式不能为空")
    private String cronExpression;

    @Schema(description = "重试次数", example = "3")
    @NotNull(message = "重试次数不能为空")
    private Integer retryCount;

    @Schema(description = "重试间隔", example = "1000")
    @NotNull(message = "重试间隔不能为空")
    private Integer retryInterval;

    @Schema(description = "监控超时时间", example = "1000")
    private Integer monitorTimeout;

}
