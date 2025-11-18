package com.basiclab.iot.device.service.device.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.device.dal.pgsql.device.DeviceTopicMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceTopic;
import com.basiclab.iot.device.service.device.DeviceTopicService;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * DeviceTopicServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class DeviceTopicServiceImpl extends ServiceImpl<DeviceTopicMapper, DeviceTopic> implements DeviceTopicService {

    /**
     * 查询设备Topic数据
     *
     * @param id 设备Topic数据主键
     * @return 设备Topic数据
     */
    @Override
    public DeviceTopic selectDeviceTopicById(Long id) {
        return baseMapper.selectDeviceTopicById(id);
    }

    /**
     * 查询设备Topic数据列表
     *
     * @param deviceTopic 设备Topic数据
     * @return 设备Topic数据
     */
    @Override
    public List<DeviceTopic> selectDeviceTopicList(DeviceTopic deviceTopic) {
        return baseMapper.selectDeviceTopicList(deviceTopic);
    }

    /**
     * 新增设备Topic数据
     *
     * @param deviceTopic 设备Topic数据
     * @return 结果
     */
    @Override
    public int insertDeviceTopic(DeviceTopic deviceTopic) {
        deviceTopic.setCreateBy("admin");
        return baseMapper.insertDeviceTopic(deviceTopic);
    }

    /**
     * 修改设备Topic数据
     *
     * @param deviceTopic 设备Topic数据
     * @return 结果
     */
    @Override
    public int updateDeviceTopic(DeviceTopic deviceTopic) {
        deviceTopic.setUpdateBy("admin");
        return baseMapper.updateDeviceTopic(deviceTopic);
    }

    /**
     * 批量删除设备Topic数据
     *
     * @param ids 需要删除的设备Topic数据主键
     * @return 结果
     */
    @Override
    public int deleteDeviceTopicByIds(Long[] ids) {
        return baseMapper.deleteDeviceTopicByIds(ids);
    }

    /**
     * 删除设备Topic数据信息
     *
     * @param id 设备Topic数据主键
     * @return 结果
     */
    @Override
    public int deleteDeviceTopicById(Long id) {
        return baseMapper.deleteDeviceTopicById(id);
    }
}
