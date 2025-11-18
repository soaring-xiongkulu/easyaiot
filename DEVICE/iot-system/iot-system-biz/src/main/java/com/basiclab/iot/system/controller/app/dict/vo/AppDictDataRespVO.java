package com.basiclab.iot.system.controller.app.dict.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * AppDictDataRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "用户 App - 字典数据信息 Response VO")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AppDictDataRespVO {

    @Schema(description = "字典数据编号", example = "1024")
    private Long id;

    @Schema(description = "字典标签", example = "BasicLab")
    private String label;

    @Schema(description = "字典值", example = "iocoder")
    private String value;

    @Schema(description = "字典类型", example = "sys_common_sex")
    private String dictType;

}
