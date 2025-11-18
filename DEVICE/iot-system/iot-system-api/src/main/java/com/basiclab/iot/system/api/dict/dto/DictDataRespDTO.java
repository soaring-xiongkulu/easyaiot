package com.basiclab.iot.system.api.dict.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "RPC 服务 - 字典数据 Response DTO")
@Data
public class DictDataRespDTO {

    @Schema

/**
 * DictDataRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

(description = "字典标签", example = "BasicLab")
    private String label;

    @Schema(description = "字典值", example = "iocoder")
    private String value;

    @Schema(description = "字典类型", example = "sys_common_sex")
    private String dictType;

    @Schema(description = "状态", example = "1")
    private Integer status; // 参见 CommonStatusEnum 枚举

}
