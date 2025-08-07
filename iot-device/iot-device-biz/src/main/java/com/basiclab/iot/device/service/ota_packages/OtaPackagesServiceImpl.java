package com.basiclab.iot.device.service.ota_packages;

import com.basiclab.iot.device.dal.mysql.ota_packages.OtaPackagesMapper;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.ota_packages.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_packages.OtaPackagesDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;


import static com.basiclab.iot.device.enums.ErrorCodeConstants.OTA_PACKAGES_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * OTA升级包 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class OtaPackagesServiceImpl implements OtaPackagesService {

    @Resource
    private OtaPackagesMapper packagesMapper;

    @Override
    public Long createPackages(OtaPackagesSaveReqVO createReqVO) {
        // 插入
        OtaPackagesDO packages = BeanUtils.toBean(createReqVO, OtaPackagesDO.class);
        packagesMapper.insert(packages);
        // 返回
        return packages.getId();
    }

    @Override
    public void updatePackages(OtaPackagesSaveReqVO updateReqVO) {
        // 校验存在
        validatePackagesExists(updateReqVO.getId());
        // 更新
        OtaPackagesDO updateObj = BeanUtils.toBean(updateReqVO, OtaPackagesDO.class);
        packagesMapper.updateById(updateObj);
    }

    @Override
    public void deletePackages(Long id) {
        // 校验存在
        validatePackagesExists(id);
        // 删除
        packagesMapper.deleteById(id);
    }

    private void validatePackagesExists(Long id) {
        if (packagesMapper.selectById(id) == null) {
            throw exception(OTA_PACKAGES_NOT_EXISTS);
        }
    }

    @Override
    public OtaPackagesDO getPackages(Long id) {
        return packagesMapper.selectById(id);
    }

    @Override
    public PageResult<OtaPackagesDO> getPackagesPage(OtaPackagesPageReqVO pageReqVO) {
        return packagesMapper.selectPage(pageReqVO);
    }

}