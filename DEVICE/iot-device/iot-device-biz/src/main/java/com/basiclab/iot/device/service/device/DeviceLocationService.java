package com.basiclab.iot.device.service.device;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.device.domain.device.vo.DeviceLocation;
import java.util.List;

/**
 * DeviceLocationService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DeviceLocationService extends IService<DeviceLocation> {

    /**
     * 查询设备位置
     *
     * @param id 设备位置主键
     * @return 设备位置
     */
    public DeviceLocation selectDeviceLocationById(Long id);

    /**
     * 查询设备位置列表
     *
     * @param deviceLocation 设备位置
     * @return 设备位置集合
     */
    public List<DeviceLocation> selectDeviceLocationList(DeviceLocation deviceLocation);

    /**
     * 新增设备位置
     *
     * @param deviceLocation 设备位置
     * @return 结果
     */
    public int insertDeviceLocation(DeviceLocation deviceLocation);

    /**
     * 修改设备位置
     *
     * @param deviceLocation 设备位置
     * @return 结果
     */
    public int updateDeviceLocation(DeviceLocation deviceLocation);

    /**
     * 批量删除设备位置
     *
     * @param ids 需要删除的设备位置主键集合
     * @return 结果
     */
    public int deleteDeviceLocationByIds(Long[] ids);



	DeviceLocation findOneByDeviceIdentification(String deviceIdentification);

}


