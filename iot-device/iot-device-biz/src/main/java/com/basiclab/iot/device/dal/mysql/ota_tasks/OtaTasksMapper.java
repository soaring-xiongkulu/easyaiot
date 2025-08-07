package com.basiclab.iot.device.dal.mysql.ota_tasks;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.ota_tasks.OtaTasksDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.ota_tasks.vo.*;

/**
 * OTA升级任务 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface OtaTasksMapper extends BaseMapperX<OtaTasksDO> {

    default PageResult<OtaTasksDO> selectPage(OtaTasksPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<OtaTasksDO>()
                .eqIfPresent(OtaTasksDO::getUpgradeId, reqVO.getUpgradeId())
                .likeIfPresent(OtaTasksDO::getTaskName, reqVO.getTaskName())
                .eqIfPresent(OtaTasksDO::getTaskStatus, reqVO.getTaskStatus())
                .betweenIfPresent(OtaTasksDO::getScheduledTime, reqVO.getScheduledTime())
                .eqIfPresent(OtaTasksDO::getDescription, reqVO.getDescription())
                .eqIfPresent(OtaTasksDO::getRemark, reqVO.getRemark())
                .eqIfPresent(OtaTasksDO::getCreatedBy, reqVO.getCreatedBy())
                .betweenIfPresent(OtaTasksDO::getCreatedTime, reqVO.getCreatedTime())
                .eqIfPresent(OtaTasksDO::getUpdatedBy, reqVO.getUpdatedBy())
                .betweenIfPresent(OtaTasksDO::getUpdatedTime, reqVO.getUpdatedTime())
                .orderByDesc(OtaTasksDO::getId));
    }

}