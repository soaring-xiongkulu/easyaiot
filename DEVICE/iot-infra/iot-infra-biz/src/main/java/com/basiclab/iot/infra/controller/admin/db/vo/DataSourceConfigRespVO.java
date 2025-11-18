package com.basiclab.iot.infra.controller.admin.db.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * DataSourceConfigRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据源配置 Response VO")
@Data
public class DataSourceConfigRespVO {

    @Schema(description = "主键编号", example = "1024")
    private Integer id;

    @Schema(description = "数据源名称", example = "test")
    private String name;

    @Schema(description = "数据源连接", example = "jdbc:mysql://127.0.0.1:3306/ruoyi-vue-pro")
    private String url;

    @Schema(description = "用户名", example = "root")
    private String username;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
