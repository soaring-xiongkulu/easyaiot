package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;

import java.io.Serializable;
import java.util.List;

/**
 * -----------------------------------------------------------------------------
 * File Name: DeviceCommandWrapperParam.java
 * -----------------------------------------------------------------------------
 * Description:
 * Device Command Request Wrapper Data Structure
 * -----------------------------------------------------------------------------
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * <p>
 * -----------------------------------------------------------------------------
 * @email andywebjava@163.com
 * @date 2023-11-11 14:55
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Builder
@ApiModel(value = "DeviceCommandWrapperParam", description = "Device Command Request Wrapper Data Structure")
public class DeviceCommandWrapperParam implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "List of serial command requests", notes = "List of serial command requests")
    private List<DeviceToGateWayVo> serial;

    @ApiModelProperty(value = "List of parallel command requests", notes = "List of parallel command requests")
    private List<DeviceToGateWayVo> parallel;
}
