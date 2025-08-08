package com.basiclab.iot.model.domain.model.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 模型量化服务分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ModelServerQuantifyPageReqVO extends PageParam {

    @Schema(description = "模型服务ID", example = "13826")
    private Long modelServeId;

    @Schema(description = "模型ID", example = "10684")
    private Long modelId;

    @Schema(description = "模型类型ID", example = "11416")
    private Long modelTypeId;

    @Schema(description = "量化服务版本号")
    private String version;

    @Schema(description = "量化时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] quantifyTime;

    @Schema(description = "量化状态[0:量化未开始,1:量化中,2:量化成功,3:量化失败]")
    private Short quantifyState;

    @Schema(description = "打包状态[0:打包未开始,1:打包中,2:打包成功,3:打包失败]")
    private Short packState;

    @Schema(description = "量化文件地址", example = "https://www.iocoder.cn")
    private String quantifyFileUrl;

    @Schema(description = "边缘平台")
    private String edgePlatform;

    @Schema(description = "芯片型号")
    private String chipModel;

    @Schema(description = "运行时环境")
    private String runEnvironment;

    @Schema(description = "开发语言")
    private String devLanguage;

    @Schema(description = "部署类型[0:压缩包下载,1:gitee拉取]", example = "1")
    private Short applyType;

    @Schema(description = "下载或拉取地址", example = "https://www.iocoder.cn")
    private String giteeUrl;

    @Schema(description = "失败原因", example = "不香")
    private String reason;

    @Schema(description = "量化备注", example = "你说的对")
    private String quantifyDescription;

    @Schema(description = "rknn存放目录")
    private String rknnDir;

}