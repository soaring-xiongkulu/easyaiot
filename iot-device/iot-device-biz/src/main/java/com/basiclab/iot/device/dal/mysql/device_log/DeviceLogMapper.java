package com.basiclab.iot.device.dal.mysql.device_log;

import com.basiclab.iot.device.dal.dataobject.device_log.DeviceLogDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.device_log.vo.*;

/**
 * 设备日志 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface DeviceLogMapper extends BaseMapperX<DeviceLogDO> {

    default PageResult<DeviceLogDO> selectPage(DeviceLogPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DeviceLogDO>()
                .eqIfPresent(DeviceLogDO::getDid, reqVO.getDid())
                .eqIfPresent(DeviceLogDO::getFileUrl, reqVO.getFileUrl())
                .betweenIfPresent(DeviceLogDO::getUploadTime, reqVO.getUploadTime())
                .likeIfPresent(DeviceLogDO::getFileName, reqVO.getFileName())
                .eqIfPresent(DeviceLogDO::getFileSize, reqVO.getFileSize())
                .eqIfPresent(DeviceLogDO::getRemark, reqVO.getRemark())
                .eqIfPresent(DeviceLogDO::getStatus, reqVO.getStatus())
                .eqIfPresent(DeviceLogDO::getCreatedBy, reqVO.getCreatedBy())
                .betweenIfPresent(DeviceLogDO::getCreatedTime, reqVO.getCreatedTime())
                .eqIfPresent(DeviceLogDO::getUpdatedBy, reqVO.getUpdatedBy())
                .betweenIfPresent(DeviceLogDO::getUpdatedTime, reqVO.getUpdatedTime())
                .orderByDesc(DeviceLogDO::getId));
    }

}