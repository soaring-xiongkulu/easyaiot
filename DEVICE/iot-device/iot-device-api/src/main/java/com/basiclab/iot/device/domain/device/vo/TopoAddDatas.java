package com.basiclab.iot.device.domain.device.vo;

import lombok.Data;

import java.util.List;

/**
 * @Description: 边设备添加子设备数据模型
 * @author EasyAIoT
 * @CreateDate: 2024/4/25$ 12:52$
 * @UpdateDate: 2024/4/25$ 12:52$
 * @Version: V1.0
 */
@Data
public class TopoAddDatas {
    private static final long serialVersionUID = 1L;
    private Integer mid;
    private List<DeviceInfo> deviceInfos;
}
