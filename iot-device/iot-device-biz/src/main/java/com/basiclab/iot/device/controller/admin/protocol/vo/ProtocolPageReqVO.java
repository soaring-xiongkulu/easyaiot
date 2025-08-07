package com.basiclab.iot.device.controller.admin.protocol.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 协议信息分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ProtocolPageReqVO extends PageParam {

    @Schema(description = "应用ID", example = "3540")
    private String appId;

    @Schema(description = "产品标识", example = "30177")
    private String pid;

    @Schema(description = "协议名称", example = "芋艿")
    private String protocolName;

    @Schema(description = "协议标识")
    private String protocolCode;

    @Schema(description = "协议版本")
    private String protocolVersion;

    @Schema(description = "协议类型 ：mqtt || coap || modbus || http", example = "1")
    private String protocolType;

    @Schema(description = "协议语言")
    private String protocolVoice;

    @Schema(description = "类名", example = "王五")
    private String className;

    @Schema(description = "文件地址")
    private String filePath;

    @Schema(description = "内容")
    private String content;

    @Schema(description = "状态(字典值：0启用  1停用)", example = "2")
    private String status;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

    @Schema(description = "备注", example = "你说的对")
    private String remark;

}