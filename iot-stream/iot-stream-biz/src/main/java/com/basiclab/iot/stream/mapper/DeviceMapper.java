package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.DeviceChannel;
import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 用于存储设备信息
 */
@Mapper
public interface DeviceMapper extends BaseMapperX<Device> {

    /**
     * 根据设备ID获取设备信息
     * @param deviceId 设备ID
     * @return 设备对象
     */
    Device getDeviceByDeviceId(@Param("deviceId") String deviceId);

    /**
     * 添加设备信息
     * @param device 设备对象
     * @return 影响的行数
     */
    int add(Device device);

    /**
     * 更新设备信息
     * @param device 设备对象
     * @return 影响的行数
     */
    int update(Device device);

    /**
     * 获取设备列表
     * @param dataType 数据类型
     * @param online 是否在线
     * @return 设备列表
     */
    List<Device> getDevices(@Param("dataType") Integer dataType, @Param("online") Boolean online);

    /**
     * 删除设备
     * @param deviceId 设备ID
     * @return 影响的行数
     */
    int del(String deviceId);

    /**
     * 获取所有在线设备
     * @return 在线设备列表
     */
    List<Device> getOnlineDevices();

    /**
     * 根据服务器ID获取在线设备
     * @param serverId 服务器ID
     * @return 在线设备列表
     */
    List<Device> getOnlineDevicesByServerId(@Param("serverId") String serverId);

    /**
     * 根据主机和端口获取设备
     * @param host 主机地址
     * @param port 端口号
     * @return 设备对象
     */
    Device getDeviceByHostAndPort(@Param("host") String host, @Param("port") int port);

    /**
     * 自定义更新设备信息
     * @param device 设备对象
     */
    void updateCustom(Device device);

    /**
     * 添加自定义设备
     * @param device 设备对象
     */
    void addCustomDevice(Device device);

    /**
     * 获取所有设备
     * @return 设备列表
     */
    List<Device> getAll();

    /**
     * 查询作为消息通道的设备
     * @return 设备列表
     */
    List<Device> queryDeviceWithAsMessageChannel();

    /**
     * 获取设备列表(带查询条件)
     * @param dataType 数据类型
     * @param query 查询条件
     * @param status 设备状态
     * @return 设备列表
     */
    List<Device> getDeviceList(@Param("dataType") Integer dataType, @Param("query") String query, @Param("status") Boolean status);

    /**
     * 获取原始通道信息
     * @param id 通道ID
     * @return 通道对象
     */
    DeviceChannel getRawChannel(@Param("id") int id);

    /**
     * 根据ID查询设备
     * @param id 设备ID
     * @return 设备对象
     */
    Device query(@Param("id") Integer id);

    /**
     * 根据通道ID查询设备
     * @param dataType 数据类型
     * @param channelId 通道ID
     * @return 设备对象
     */
    Device queryByChannelId(@Param("dataType") Integer dataType, @Param("channelId") Integer channelId);

    /**
     * 根据源通道设备ID获取设备
     * @param dataType 数据类型
     * @param channelDeviceId 通道设备ID
     * @return 设备对象
     */
    Device getDeviceBySourceChannelDeviceId(@Param("dataType") Integer dataType, @Param("channelDeviceId") String channelDeviceId);

    /**
     * 更新设备目录订阅周期
     * @param device 设备对象
     */
    void updateSubscribeCatalog(Device device);

    /**
     * 更新设备移动位置订阅周期
     * @param device 设备对象
     */
    void updateSubscribeMobilePosition(Device device);

    /**
     * 批量设置设备离线状态
     * @param offlineDevices 离线设备列表
     */
    void offlineByList(List<Device> offlineDevices);
}
