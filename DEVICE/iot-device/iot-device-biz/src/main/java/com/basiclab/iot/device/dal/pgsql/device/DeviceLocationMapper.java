package com.basiclab.iot.device.dal.pgsql.device;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceLocation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * DeviceLocationMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DeviceLocationMapper extends BaseMapper<DeviceLocation> {

    /**
     * 查询设备位置
     *
     * @param id 设备位置主键
     * @return 设备位置
     */
    DeviceLocation selectDeviceLocationById(Long id);

    /**
     * 查询设备位置列表
     *
     * @param deviceLocation 设备位置
     * @return 设备位置集合
     */
    List<DeviceLocation> selectDeviceLocationList(DeviceLocation deviceLocation);

    /**
     * 新增设备位置
     *
     * @param deviceLocation 设备位置
     * @return 结果
     */
    int insertDeviceLocation(DeviceLocation deviceLocation);

    /**
     * 修改设备位置
     *
     * @param deviceLocation 设备位置
     * @return 结果
     */
    int updateDeviceLocation(DeviceLocation deviceLocation);

    /**
     * 批量删除设备位置
     *
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteDeviceLocationByIds(Long[] ids);

    DeviceLocation findOneByDeviceIdentification(@Param("deviceIdentification")String deviceIdentification);
}
