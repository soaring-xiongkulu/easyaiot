package com.basiclab.iot.infra.controller.admin.file.vo.config;

import com.basiclab.iot.infra.framework.file.core.client.FileClientConfig;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * FileConfigRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 文件配置 Response VO")
@Data
public class FileConfigRespVO {

    @Schema(description = "编号", example = "1")
    private Long id;

    @Schema(description = "配置名", example = "S3 - 阿里云")
    private String name;

    @Schema(description = "存储器，参见 FileStorageEnum 枚举类", example = "1")
    private Integer storage;

    @Schema(description = "是否为主配置", example = "true")
    private Boolean master;

    @Schema(description = "存储配置")
    private FileClientConfig config;

    @Schema(description = "备注", example = "我是备注")
    private String remark;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
