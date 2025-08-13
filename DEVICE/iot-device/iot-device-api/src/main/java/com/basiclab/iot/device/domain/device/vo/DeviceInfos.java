package com.basiclab.iot.device.domain.device.vo;

import lombok.Data;

/**
 * @Description:  边设备添加子设备详情数据模型
 * @author EasyAIoT
 * @CreateDate: 2024/4/25$ 12:54$
 * @UpdateDate: 2024/4/25$ 12:54$
 * @Version: V1.0
 */
@Data
public class DeviceInfos {
    private static final long serialVersionUID = 1L;
    private String nodeId;
    private String name;
    private String description;
    private String manufacturerId;
    private String model;
}
