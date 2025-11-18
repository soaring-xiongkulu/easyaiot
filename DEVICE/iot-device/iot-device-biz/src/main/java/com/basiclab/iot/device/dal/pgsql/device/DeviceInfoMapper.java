package com.basiclab.iot.device.dal.pgsql.device;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.DeviceInfo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Collection;
import java.util.List;

/**
 * DeviceInfoMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DeviceInfoMapper extends BaseMapper<DeviceInfo> {

    int deleteByDeviceId(@Param("deviceId")String deviceId);

    DeviceInfo findOneByDeviceId(@Param("deviceId")String deviceId);

    /**
     * 查询子设备管理
     *
     * @param id 子设备管理主键
     * @return 子设备管理
     */
    DeviceInfo selectDeviceInfoById(Long id);

    /**
     * 查询子设备管理列表
     *
     * @param deviceInfo 子设备管理
     * @return 子设备管理集合
     */
    List<DeviceInfo> selectDeviceInfoList(DeviceInfo deviceInfo);

    /**
     * 新增子设备管理
     *
     * @param deviceInfo 子设备管理
     * @return 结果
     */
    int insertDeviceInfo(DeviceInfo deviceInfo);

    /**
     * 修改子设备管理
     *
     * @param deviceInfo 子设备管理
     * @return 结果
     */
    int updateDeviceInfo(DeviceInfo deviceInfo);

    /**
     * 删除子设备管理
     *
     * @param id 子设备管理主键
     * @return 结果
     */
    int deleteDeviceInfoById(Long id);

    /**
     * 批量删除子设备管理
     *
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteDeviceInfoByIds(Long[] ids);

    List<DeviceInfo> findAllByIdInAndStatus(@Param("idCollection")Collection<Long> idCollection,@Param("status")String status);

    List<DeviceInfo> findAllByIdIn(@Param("idCollection")Collection<Long> idCollection);

    List<DeviceInfo> findAllByStatus(@Param("status")String status);
}
