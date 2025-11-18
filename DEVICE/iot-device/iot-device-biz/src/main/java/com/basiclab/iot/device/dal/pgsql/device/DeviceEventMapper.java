package com.basiclab.iot.device.dal.pgsql.device;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceEvent;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * DeviceEventMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DeviceEventMapper extends BaseMapper<DeviceEvent> {

    /**
     * 查询设备事件列表
     *
     * @param deviceEvent 查询条件
     * @return 设备事件列表
     */
    List<DeviceEvent> selectDeviceEventList(DeviceEvent deviceEvent);

    /**
     * 根据ID查询设备事件
     *
     * @param id 主键ID
     * @return 设备事件
     */
    DeviceEvent selectDeviceEventById(@Param("id") Long id);

    /**
     * 新增设备事件
     *
     * @param deviceEvent 设备事件
     * @return 影响行数
     */
    int insertDeviceEvent(DeviceEvent deviceEvent);

    /**
     * 更新设备事件
     *
     * @param deviceEvent 设备事件
     * @return 影响行数
     */
    int updateDeviceEvent(DeviceEvent deviceEvent);

    /**
     * 批量删除设备事件
     *
     * @param ids ID数组
     * @return 影响行数
     */
    int deleteDeviceEventByIds(@Param("array") String[] ids);
}

