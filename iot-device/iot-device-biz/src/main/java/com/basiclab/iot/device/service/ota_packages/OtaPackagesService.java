package com.basiclab.iot.device.service.ota_packages;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.ota_packages.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_packages.OtaPackagesDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * OTA升级包 Service 接口
 *
 * @author BasicLab
 */
public interface OtaPackagesService {

    /**
     * 创建OTA升级包
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createPackages(@Valid OtaPackagesSaveReqVO createReqVO);

    /**
     * 更新OTA升级包
     *
     * @param updateReqVO 更新信息
     */
    void updatePackages(@Valid OtaPackagesSaveReqVO updateReqVO);

    /**
     * 删除OTA升级包
     *
     * @param id 编号
     */
    void deletePackages(Long id);

    /**
     * 获得OTA升级包
     *
     * @param id 编号
     * @return OTA升级包
     */
    OtaPackagesDO getPackages(Long id);

    /**
     * 获得OTA升级包分页
     *
     * @param pageReqVO 分页查询
     * @return OTA升级包分页
     */
    PageResult<OtaPackagesDO> getPackagesPage(OtaPackagesPageReqVO pageReqVO);

}