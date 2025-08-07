package com.basiclab.iot.device.dal.mysql.ota_packages;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.ota_packages.OtaPackagesDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.ota_packages.vo.*;

/**
 * OTA升级包 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface OtaPackagesMapper extends BaseMapperX<OtaPackagesDO> {

    default PageResult<OtaPackagesDO> selectPage(OtaPackagesPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<OtaPackagesDO>()
                .eqIfPresent(OtaPackagesDO::getAppId, reqVO.getAppId())
                .likeIfPresent(OtaPackagesDO::getPackageName, reqVO.getPackageName())
                .eqIfPresent(OtaPackagesDO::getPackageType, reqVO.getPackageType())
                .eqIfPresent(OtaPackagesDO::getProductIdentification, reqVO.getProductIdentification())
                .eqIfPresent(OtaPackagesDO::getVersion, reqVO.getVersion())
                .eqIfPresent(OtaPackagesDO::getFileLocation, reqVO.getFileLocation())
                .eqIfPresent(OtaPackagesDO::getStatus, reqVO.getStatus())
                .eqIfPresent(OtaPackagesDO::getDescription, reqVO.getDescription())
                .eqIfPresent(OtaPackagesDO::getCustomInfo, reqVO.getCustomInfo())
                .eqIfPresent(OtaPackagesDO::getRemark, reqVO.getRemark())
                .eqIfPresent(OtaPackagesDO::getCreatedBy, reqVO.getCreatedBy())
                .betweenIfPresent(OtaPackagesDO::getCreatedTime, reqVO.getCreatedTime())
                .eqIfPresent(OtaPackagesDO::getUpdatedBy, reqVO.getUpdatedBy())
                .betweenIfPresent(OtaPackagesDO::getUpdatedTime, reqVO.getUpdatedTime())
                .orderByDesc(OtaPackagesDO::getId));
    }

}