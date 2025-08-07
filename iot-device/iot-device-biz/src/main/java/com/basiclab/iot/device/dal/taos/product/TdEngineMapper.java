package com.basiclab.iot.device.dal.taos.product;

import com.basiclab.iot.device.dal.dataobject.product.DeviceData;
import com.basiclab.iot.device.dal.dataobject.product.TDDeviceDataRequest;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface TdEngineMapper {

    /**
     * 通过设备标识查询设备最新数据
     *
     * @param tdDeviceDataRequest 请求体
     * @return DeviceData
     */
    List<DeviceData> getLastRowsListByIdentifier(TDDeviceDataRequest tdDeviceDataRequest);
}
