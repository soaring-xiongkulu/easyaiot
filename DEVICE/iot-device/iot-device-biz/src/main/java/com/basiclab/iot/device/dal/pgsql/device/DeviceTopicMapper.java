package com.basiclab.iot.device.dal.pgsql.device;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceTopic;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * DeviceTopicMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DeviceTopicMapper extends BaseMapper<DeviceTopic> {

    /**
     * 查询设备Topic数据
     *
     * @param id 设备Topic数据主键
     * @return 设备Topic数据
     */
    DeviceTopic selectDeviceTopicById(Long id);

    /**
     * 查询设备Topic数据列表
     *
     * @param deviceTopic 设备Topic数据
     * @return 设备Topic数据集合
     */
    List<DeviceTopic> selectDeviceTopicList(DeviceTopic deviceTopic);

    /**
     * 新增设备Topic数据
     *
     * @param deviceTopic 设备Topic数据
     * @return 结果
     */
    int insertDeviceTopic(DeviceTopic deviceTopic);

    /**
     * 修改设备Topic数据
     *
     * @param deviceTopic 设备Topic数据
     * @return 结果
     */
    int updateDeviceTopic(DeviceTopic deviceTopic);

    /**
     * 删除设备Topic数据
     *
     * @param id 设备Topic数据主键
     * @return 结果
     */
    int deleteDeviceTopicById(Long id);

    /**
     * 批量删除设备Topic数据
     *
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteDeviceTopicByIds(Long[] ids);
}
