package com.basiclab.iot.device.domain.protocol.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc    协议传输对象
 * @created 2025-06-21
 */
@ApiModel(value="协议缓存信息更新传输对象")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class ProtocolDto {

    @ApiModelProperty(value="需要更新的协议的协议主键ID集合")
    private List<Long> protocolIds;

    @ApiModelProperty(value="操作类型： DELETE 清理设备脚本内存   FLUSH 刷新设备缓存   CLEAR 清空所有设备的脚本内存")
    private String operateType;

}
