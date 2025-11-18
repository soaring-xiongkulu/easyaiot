package com.basiclab.iot.system.controller.admin.dict.vo.type;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * DictTypeSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 字典类型精简信息 Response VO")
@Data
public class DictTypeSimpleRespVO {

    @Schema(description = "字典类型编号", example = "1024")
    private Long id;

    @Schema(description = "字典类型名称", example = "BasicLab")
    private String name;

    @Schema(description = "字典类型", example = "sys_common_sex")
    private String type;

}
