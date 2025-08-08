package com.basiclab.iot.model.domain.model.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 模型服务分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ModelServerPageReqVO extends PageParam {

    @Schema(description = "模型服务名称", example = "王五")
    private String name;

    @Schema(description = "模型ID", example = "5092")
    private Long modelId;

    @Schema(description = "数据集ID", example = "21514")
    private Long datasetId;

    @Schema(description = "发布状态[0:待发布,1:已发布,2:发布失败,3:已下架]", example = "1")
    private Short publishStatus;

    @Schema(description = "审核人ID", example = "530")
    private Long auditUserId;

    @Schema(description = "版本号")
    private String version;

    @Schema(description = "服务访问地址")
    private String serverAddress;

    @Schema(description = "ONNX模型文件", example = "https://www.iocoder.cn")
    private String onnxFileUrl;

    @Schema(description = "描述", example = "你说的对")
    private String description;

    @Schema(description = "模型大小")
    private Long size;

    @Schema(description = "执行状态[0:未启动,1:部署中,2:部署失败,3:运行中,4:已关闭]", example = "1")
    private Short executeStatus;

    @Schema(description = "发布时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] publishTime;

    @Schema(description = "anchors.txt文件", example = "https://www.iocoder.cn")
    private String anchorsFileUrl;

    @Schema(description = "完整应用文件（或量化后应用文件）", example = "https://www.iocoder.cn")
    private String applyFileUrl;

    @Schema(description = "应用文件大小")
    private Long applyFileSize;

    @Schema(description = "应用文件MD5值")
    private String applyFileMd5;

}