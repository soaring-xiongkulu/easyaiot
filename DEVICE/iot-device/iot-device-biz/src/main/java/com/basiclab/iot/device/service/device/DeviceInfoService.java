package com.basiclab.iot.device.service.device;

import com.basiclab.iot.device.domain.device.vo.*;

import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * @Description: 子设备档案接口
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @Version: V1.0
 */
public interface DeviceInfoService {

    int deleteByPrimaryKey(Long id);

    int insert(DeviceInfo record);

    int insertOrUpdate(DeviceInfo record);

    int insertOrUpdateSelective(DeviceInfo record);

    int insertSelective(DeviceInfo record);

    DeviceInfo selectByPrimaryKey(Long id);

    int updateByPrimaryKeySelective(DeviceInfo record);

    int updateByPrimaryKey(DeviceInfo record);

    int updateBatch(List<DeviceInfo> list);

    int batchInsert(List<DeviceInfo> list);


    int deleteByDeviceId(String deviceId);


    DeviceInfo findOneByDeviceId(String deviceId);

    /**
     * 查询子设备管理
     *
     * @param id 子设备管理主键
     * @return 子设备管理
     */
    public DeviceInfo selectDeviceInfoById(Long id);

    /**
     * 查询子设备管理列表
     *
     * @param deviceInfo 子设备管理
     * @return 子设备管理集合
     */
    public List<DeviceInfo> selectDeviceInfoList(DeviceInfo deviceInfo);

    /**
     * 新增子设备管理
     *
     * @param deviceInfoParams
     * @return 结果
     */
    public int insertDeviceInfo(DeviceInfoParams deviceInfoParams);

    /**
     * 修改子设备管理
     *
     * @param deviceInfoParams 子设备管理
     * @return 结果
     */
    public int updateDeviceInfo(DeviceInfoParams deviceInfoParams);

    /**
     * 批量删除子设备管理
     *
     * @param ids 需要删除的子设备管理主键集合
     * @return 结果
     */
    public int deleteDeviceInfoByIds(Long[] ids);

    /**
     * 查询子设备影子数据
     *
     * @param ids       需要查询的子设备id
     * @param startTime 开始时间 格式：yyyy-MM-dd HH:mm:ss
     * @param endTime   结束时间 格式：yyyy-MM-dd HH:mm:ss
     * @return 子设备影子数据
     */
    public Map<String, List<Map<String, Object>>> getDeviceInfoShadow(String ids, String startTime, String endTime);


    List<DeviceInfo> findAllByIdInAndStatus(Collection<Long> idCollection, String status);


    List<DeviceInfo> findAllByIdIn(Collection<Long> idCollection);

    List<DeviceInfo> findAllByStatus(String status);

}


