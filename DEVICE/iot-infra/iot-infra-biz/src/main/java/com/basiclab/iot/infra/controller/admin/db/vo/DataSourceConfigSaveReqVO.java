package com.basiclab.iot.infra.controller.admin.db.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

/**
 * DataSourceConfigSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据源配置创建/修改 Request VO")
@Data
public class DataSourceConfigSaveReqVO {

    @Schema(description = "主键编号", example = "1024")
    private Long id;

    @Schema(description = "数据源名称", example = "test")
    @NotNull(message = "数据源名称不能为空")
    private String name;

    @Schema(description = "数据源连接", example = "jdbc:mysql://127.0.0.1:3306/ruoyi-vue-pro")
    @NotNull(message = "数据源连接不能为空")
    private String url;

    @Schema(description = "用户名", example = "root")
    @NotNull(message = "用户名不能为空")
    private String username;

    @Schema(description = "密码", example = "123456")
    @NotNull(message = "密码不能为空")
    private String password;

}
