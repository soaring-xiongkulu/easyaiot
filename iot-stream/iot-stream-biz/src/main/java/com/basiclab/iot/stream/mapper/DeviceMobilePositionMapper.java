package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.MobilePosition;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface DeviceMobilePositionMapper extends BaseMapperX<MobilePosition> {

    /**
     * 插入新的移动位置记录
     * @param mobilePosition 移动位置对象
     * @return 影响的行数
     */
    int insertNewPosition(MobilePosition mobilePosition);

    /**
     * 根据设备ID和时间范围查询位置记录
     * @param deviceId 设备ID
     * @param channelId 通道ID
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return 位置记录列表
     */
    List<MobilePosition> queryPositionByDeviceIdAndTime(@Param("deviceId") String deviceId, @Param("channelId") String channelId, @Param("startTime") String startTime, @Param("endTime") String endTime);

    /**
     * 查询设备最新的位置记录
     * @param deviceId 设备ID
     * @return 最新的位置记录
     */
    MobilePosition queryLatestPositionByDevice(String deviceId);

    /**
     * 清除设备的所有位置记录
     * @param deviceId 设备ID
     * @return 影响的行数
     */
    int clearMobilePositionsByDeviceId(String deviceId);

    /**
     * 批量添加位置记录
     * @param mobilePositions 位置记录列表
     */
    void batchadd(List<MobilePosition> mobilePositions);

}
