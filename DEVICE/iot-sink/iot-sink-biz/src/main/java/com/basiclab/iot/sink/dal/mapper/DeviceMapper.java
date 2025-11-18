package com.basiclab.iot.sink.dal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * DeviceMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
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

    /**
     * 更新设备连接状态和最后在线时间
     *
     * @param deviceId 设备ID
     * @param connectStatus 连接状态
     * @param lastOnlineTime 最后在线时间
     * @return 更新行数
     */
    int updateDeviceConnectStatus(@Param("deviceId") Long deviceId,
                                   @Param("connectStatus") String connectStatus,
                                   @Param("lastOnlineTime") java.time.LocalDateTime lastOnlineTime);

    /**
     * 更新设备扩展信息
     *
     * @param deviceId 设备ID
     * @param extension 扩展信息（JSON字符串）
     * @return 更新行数
     */
    int updateDeviceExtension(@Param("deviceId") Long deviceId,
                              @Param("extension") String extension);

    /**
     * 更新设备版本信息
     *
     * @param deviceId 设备ID
     * @param deviceVersion 设备版本
     * @return 更新行数
     */
    int updateDeviceVersion(@Param("deviceId") Long deviceId,
                            @Param("deviceVersion") String deviceVersion);

    /**
     * 更新设备标签信息
     *
     * @param deviceId 设备ID
     * @param tags 标签信息（JSON字符串）
     * @return 更新行数
     */
    int updateDeviceTags(@Param("deviceId") Long deviceId,
                         @Param("tags") String tags);

    /**
     * 更新设备影子状态
     *
     * @param deviceId 设备ID
     * @param shadow 影子状态（JSON字符串）
     * @return 更新行数
     */
    int updateDeviceShadow(@Param("deviceId") Long deviceId,
                           @Param("shadow") String shadow);

    /**
     * 更新设备配置信息
     *
     * @param deviceId 设备ID
     * @param config 配置信息（JSON字符串）
     * @return 更新行数
     */
    int updateDeviceConfig(@Param("deviceId") Long deviceId,
                           @Param("config") String config);

    /**
     * 更新设备OTA进度
     *
     * @param deviceId 设备ID
     * @param otaProgress OTA进度（JSON字符串）
     * @return 更新行数
     */
    int updateDeviceOtaProgress(@Param("deviceId") Long deviceId,
                                 @Param("otaProgress") String otaProgress);
}

