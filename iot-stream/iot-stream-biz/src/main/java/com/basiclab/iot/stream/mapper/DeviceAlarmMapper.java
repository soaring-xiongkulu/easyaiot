package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.DeviceAlarm;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 用于存储设备的报警信息
 */
@Mapper
public interface DeviceAlarmMapper extends BaseMapperX<DeviceAlarm> {

    /**
     * 添加报警信息
     *
     * @param alarm 报警信息实体
     * @return 插入结果
     */
    int add(DeviceAlarm alarm);

    /**
     * 查询报警信息
     *
     * @param deviceId      设备ID
     * @param alarmPriority 报警优先级
     * @param alarmMethod   报警方式
     * @param alarmType     报警类型
     * @param startTime     开始时间
     * @param endTime       结束时间
     * @return 报警信息列表
     */
    List<DeviceAlarm> query(@Param("deviceId") String deviceId, @Param("alarmPriority") String alarmPriority, @Param("alarmMethod") String alarmMethod,
                            @Param("alarmType") String alarmType, @Param("startTime") String startTime, @Param("endTime") String endTime);

    /**
     * 清除报警信息
     *
     * @param id           报警信息ID
     * @param deviceIdList 设备ID列表
     * @param time         时间
     * @return 删除结果
     */
    int clearAlarmBeforeTime(@Param("id") Integer id, @Param("deviceIdList") List<String> deviceIdList, @Param("time") String time);
}