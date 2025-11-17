package com.basiclab.iot.sink.dal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 设备 Mapper
 *
 * @author 翱翔的雄库鲁
 */
@Mapper
public interface DeviceMapper extends BaseMapper<DeviceDO> {

    /**
     * 根据产品唯一标识和设备唯一标识查询设备
     *
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification 设备唯一标识
     * @return 设备信息
     */
    DeviceDO selectByProductIdentificationAndDeviceIdentification(@Param("productIdentification") String productIdentification,
                                                                  @Param("deviceIdentification") String deviceIdentification);

    /**
     * 根据ID查询设备
     *
     * @param id 设备ID
     * @return 设备信息
     */
    DeviceDO selectById(@Param("id") Long id);

    /**
     * 根据客户端ID、用户名、密码、设备状态和协议类型查询设备（用于认证）
     *
     * @param clientId 客户端ID
     * @param userName 用户名
     * @param password 密码
     * @param deviceStatus 设备状态
     * @param protocolType 协议类型
     * @return 设备信息
     */
    DeviceDO selectByClientIdAndUserNameAndPasswordAndDeviceStatusAndProtocolType(
            @Param("clientId") String clientId,
            @Param("userName") String userName,
            @Param("password") String password,
            @Param("deviceStatus") String deviceStatus,
            @Param("protocolType") String protocolType);
}

