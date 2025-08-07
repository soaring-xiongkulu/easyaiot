package com.basiclab.iot.device.service.device_log;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.device_log.vo.*;
import com.basiclab.iot.device.dal.dataobject.device_log.DeviceLogDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 设备日志 Service 接口
 *
 * @author BasicLab
 */
public interface DeviceLogService {

    /**
     * 创建设备日志
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createLog(@Valid DeviceLogSaveReqVO createReqVO);

    /**
     * 更新设备日志
     *
     * @param updateReqVO 更新信息
     */
    void updateLog(@Valid DeviceLogSaveReqVO updateReqVO);

    /**
     * 删除设备日志
     *
     * @param id 编号
     */
    void deleteLog(Long id);

    /**
     * 获得设备日志
     *
     * @param id 编号
     * @return 设备日志
     */
    DeviceLogDO getLog(Long id);

    /**
     * 获得设备日志分页
     *
     * @param pageReqVO 分页查询
     * @return 设备日志分页
     */
    PageResult<DeviceLogDO> getLogPage(DeviceLogPageReqVO pageReqVO);

}