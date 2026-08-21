package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.node.dal.dataobject.DeviceMediaBindingDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DeviceMediaBindingMapper extends BaseMapperX<DeviceMediaBindingDO> {

    default DeviceMediaBindingDO selectByDeviceId(String deviceId) {
        return selectOne(DeviceMediaBindingDO::getDeviceId, deviceId);
    }

}
