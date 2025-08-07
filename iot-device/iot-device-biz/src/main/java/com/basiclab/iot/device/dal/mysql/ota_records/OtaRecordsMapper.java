package com.basiclab.iot.device.dal.mysql.ota_records;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.ota_records.OtaRecordsDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.ota_records.vo.*;

/**
 * OTA升级记录 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface OtaRecordsMapper extends BaseMapperX<OtaRecordsDO> {

    default PageResult<OtaRecordsDO> selectPage(OtaRecordsPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<OtaRecordsDO>()
                .eqIfPresent(OtaRecordsDO::getTaskId, reqVO.getTaskId())
                .eqIfPresent(OtaRecordsDO::getDid, reqVO.getDid())
                .eqIfPresent(OtaRecordsDO::getUpgradeStatus, reqVO.getUpgradeStatus())
                .eqIfPresent(OtaRecordsDO::getProgress, reqVO.getProgress())
                .eqIfPresent(OtaRecordsDO::getErrorCode, reqVO.getErrorCode())
                .eqIfPresent(OtaRecordsDO::getErrorMessage, reqVO.getErrorMessage())
                .betweenIfPresent(OtaRecordsDO::getStartTime, reqVO.getStartTime())
                .betweenIfPresent(OtaRecordsDO::getEndTime, reqVO.getEndTime())
                .eqIfPresent(OtaRecordsDO::getSuccessDetails, reqVO.getSuccessDetails())
                .eqIfPresent(OtaRecordsDO::getFailureDetails, reqVO.getFailureDetails())
                .eqIfPresent(OtaRecordsDO::getLogDetails, reqVO.getLogDetails())
                .eqIfPresent(OtaRecordsDO::getRemark, reqVO.getRemark())
                .betweenIfPresent(OtaRecordsDO::getCreatedTime, reqVO.getCreatedTime())
                .eqIfPresent(OtaRecordsDO::getCreatedBy, reqVO.getCreatedBy())
                .eqIfPresent(OtaRecordsDO::getUpdatedBy, reqVO.getUpdatedBy())
                .betweenIfPresent(OtaRecordsDO::getUpdatedTime, reqVO.getUpdatedTime())
                .orderByDesc(OtaRecordsDO::getId));
    }

}