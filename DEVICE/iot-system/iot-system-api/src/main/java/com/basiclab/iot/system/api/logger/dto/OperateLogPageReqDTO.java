package com.basiclab.iot.system.api.logger.dto;

import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * OperateLogPageReqDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(name = "RPC 服务 - 操作日志分页 Request DTO")
@Data
public class OperateLogPageReqDTO extends PageParam {

    @Schema(description = "模块类型", example = "订单")
    private String type;

    @Schema(description = "模块数据编号", example = "188")
    private Long bizId;

    @Schema(description = "用户编号", example = "666")
    private Long userId;

}
