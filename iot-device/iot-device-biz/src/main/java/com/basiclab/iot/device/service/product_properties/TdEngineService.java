package com.basiclab.iot.device.service.product_properties;

import com.basiclab.iot.device.dal.dataobject.product.DeviceData;
import com.basiclab.iot.device.dal.dataobject.product.TDDeviceDataRequest;

import java.util.List;

/**
 * @InterfaceDescription: TdEngine业务层
 * @InterfaceName: ITdEngineService
 * @Author: iot
 * @Date: 2021-12-27 13:54:58
 * @Version 1.0
 */
public interface TdEngineService {
    /**
     * 通过设备标识查询设备最新数据
     *
     * @param tdDeviceDataRequest 请求体
     * @return DeviceData
     */
    List<DeviceData> getLastRowsListByIdentifier(TDDeviceDataRequest tdDeviceDataRequest);

}
