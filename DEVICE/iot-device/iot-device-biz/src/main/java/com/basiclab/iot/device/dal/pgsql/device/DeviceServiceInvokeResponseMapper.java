package com.basiclab.iot.device.dal.pgsql.device;

import com.basiclab.iot.device.domain.device.vo.DeviceServiceInvokeResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * DeviceServiceInvokeResponseMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DeviceServiceInvokeResponseMapper {

    /**
     * 插入记录
     *
     * @param record 记录
     * @return 插入数量
     */
    int insert(DeviceServiceInvokeResponse record);

    /**
     * 根据主键查询
     *
     * @param id 主键
     * @return 记录
     */
    DeviceServiceInvokeResponse selectByPrimaryKey(@Param("id") Long id);

    /**
     * 根据消息ID查询
     *
     * @param messageId 消息ID
     * @return 记录
     */
    DeviceServiceInvokeResponse selectByMessageId(@Param("messageId") String messageId);

    /**
     * 根据设备ID查询
     *
     * @param deviceId 设备ID
     * @return 记录列表
     */
    List<DeviceServiceInvokeResponse> selectByDeviceId(@Param("deviceId") Long deviceId);
}

