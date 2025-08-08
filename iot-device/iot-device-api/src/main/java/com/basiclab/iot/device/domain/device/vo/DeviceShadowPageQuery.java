package com.basiclab.iot.device.domain.device.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;

/**
 * -----------------------------------------------------------------------------
 * File Name: DeviceShadowPageQuery
 * -----------------------------------------------------------------------------
 * Description:
 * 设备影子查询参数
 * -----------------------------------------------------------------------------
 *
 * @author EasyAIoT
 * @version 1.0
 * -----------------------------------------------------------------------------
 * Revision History:
 * Date         Author          Version     Description
 * --------      --------     -------   --------------------
 * 2024/3/26       basiclab        1.0        Initial creation
 * -----------------------------------------------------------------------------
 * @email andywebjava@163.com
 * @date 2024/3/26 19:21
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@EqualsAndHashCode
@Builder
@ApiModel(value = "DeviceShadowPageQuery", description = "设备影子信息分页参数")
public class DeviceShadowPageQuery implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 设备标识
     */
    @ApiModelProperty(name = "deviceIdentification", value = "设备标识")
    private String deviceIdentification;

    /**
     * 开始时间
     */
    @ApiModelProperty(name = "startTime", value = "开始时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private String startTime;

    /**
     * 结束时间
     */
    @ApiModelProperty(name = "endTime", value = "结束时间戳")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private String endTime;
}

