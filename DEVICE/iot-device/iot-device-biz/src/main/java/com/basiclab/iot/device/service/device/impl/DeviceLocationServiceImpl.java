package com.basiclab.iot.device.service.device.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.utils.SecurityUtils;
import com.basiclab.iot.device.dal.pgsql.device.DeviceLocationMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceLocation;
import com.basiclab.iot.device.service.device.DeviceLocationService;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * DeviceLocationServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class DeviceLocationServiceImpl extends ServiceImpl<DeviceLocationMapper, DeviceLocation> implements DeviceLocationService {

    /**
     * 查询设备位置
     *
     * @param id 设备位置主键
     * @return 设备位置
     */
    @Override
    public DeviceLocation selectDeviceLocationById(Long id) {
        return baseMapper.selectDeviceLocationById(id);
    }

    /**
     * 查询设备位置列表
     *
     * @param deviceLocation 设备位置
     * @return 设备位置
     */
    @Override
    public List<DeviceLocation> selectDeviceLocationList(DeviceLocation deviceLocation) {
        return baseMapper.selectDeviceLocationList(deviceLocation);
    }

    /**
     * 新增设备位置
     *
     * @param deviceLocation 设备位置
     * @return 结果
     */
    @Override
    public int insertDeviceLocation(DeviceLocation deviceLocation) {
        deviceLocation.setCreateBy(SecurityUtils.getUsername());
        return baseMapper.insertDeviceLocation(deviceLocation);
    }

    /**
     * 修改设备位置
     *
     * @param deviceLocation 设备位置
     * @return 结果
     */
    @Override
    public int updateDeviceLocation(DeviceLocation deviceLocation) {
        deviceLocation.setUpdateBy(SecurityUtils.getUsername());
        return baseMapper.updateDeviceLocation(deviceLocation);
    }

    /**
     * 批量删除设备位置
     *
     * @param ids 需要删除的设备位置主键
     * @return 结果
     */
    @Override
    public int deleteDeviceLocationByIds(Long[] ids) {
        return baseMapper.deleteDeviceLocationByIds(ids);
    }

    @Override
    public DeviceLocation findOneByDeviceIdentification(String deviceIdentification) {
        return baseMapper.findOneByDeviceIdentification(deviceIdentification);
    }


}


