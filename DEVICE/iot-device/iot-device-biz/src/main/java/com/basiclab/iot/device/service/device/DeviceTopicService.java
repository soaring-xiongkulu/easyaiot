package com.basiclab.iot.device.service.device;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.device.domain.device.vo.DeviceTopic;

import java.util.List;

/**
 * DeviceTopicService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DeviceTopicService extends IService<DeviceTopic> {

    /**
     * 查询设备Topic数据
     *
     * @param id 设备Topic数据主键
     * @return 设备Topic数据
     */
    public DeviceTopic selectDeviceTopicById(Long id);

    /**
     * 查询设备Topic数据列表
     *
     * @param deviceTopic 设备Topic数据
     * @return 设备Topic数据集合
     */
    public List<DeviceTopic> selectDeviceTopicList(DeviceTopic deviceTopic);

    /**
     * 新增设备Topic数据
     *
     * @param deviceTopic 设备Topic数据
     * @return 结果
     */
    public int insertDeviceTopic(DeviceTopic deviceTopic);

    /**
     * 修改设备Topic数据
     *
     * @param deviceTopic 设备Topic数据
     * @return 结果
     */
    public int updateDeviceTopic(DeviceTopic deviceTopic);

    /**
     * 批量删除设备Topic数据
     *
     * @param ids 需要删除的设备Topic数据主键集合
     * @return 结果
     */
    public int deleteDeviceTopicByIds(Long[] ids);

    /**
     * 删除设备Topic数据信息
     *
     * @param id 设备Topic数据主键
     * @return 结果
     */
    public int deleteDeviceTopicById(Long id);

}
