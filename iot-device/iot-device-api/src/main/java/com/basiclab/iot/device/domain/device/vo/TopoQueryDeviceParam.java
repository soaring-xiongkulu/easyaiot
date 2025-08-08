package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.util.List;

/**
 * @Description: 查询设备信息数据模型
 * @author EasyAIoT
 * @CreateDate: 2024/4/25$ 12:52$
 * @UpdateDate: 2024/01/10$ 12:52$
 * @Version: V1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@EqualsAndHashCode
@Builder
@ApiModel(value = "TopoQueryDeviceParam", description = "查询设备信息数据模型")
public class TopoQueryDeviceParam implements Serializable {
    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "设备标识集合", notes = "设备标识集合")
    @NotNull(message = "设备标识集合不能为空")
    private List<String> deviceIds;
}
