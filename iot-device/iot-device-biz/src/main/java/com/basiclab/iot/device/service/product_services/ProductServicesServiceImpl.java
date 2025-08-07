package com.basiclab.iot.device.service.product_services;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_services.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_services.ProductServicesDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_services.ProductServicesMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_SERVICES_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模型服务 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductServicesServiceImpl implements ProductServicesService {

    @Resource
    private ProductServicesMapper servicesMapper;

    @Override
    public Long createServices(ProductServicesSaveReqVO createReqVO) {
        // 插入
        ProductServicesDO services = BeanUtils.toBean(createReqVO, ProductServicesDO.class);
        servicesMapper.insert(services);
        // 返回
        return services.getId();
    }

    @Override
    public void updateServices(ProductServicesSaveReqVO updateReqVO) {
        // 校验存在
        validateServicesExists(updateReqVO.getId());
        // 更新
        ProductServicesDO updateObj = BeanUtils.toBean(updateReqVO, ProductServicesDO.class);
        servicesMapper.updateById(updateObj);
    }

    @Override
    public void deleteServices(Long id) {
        // 校验存在
        validateServicesExists(id);
        // 删除
        servicesMapper.deleteById(id);
    }

    private void validateServicesExists(Long id) {
        if (servicesMapper.selectById(id) == null) {
            throw exception(PRODUCT_SERVICES_NOT_EXISTS);
        }
    }

    @Override
    public ProductServicesDO getServices(Long id) {
        return servicesMapper.selectById(id);
    }

    @Override
    public PageResult<ProductServicesDO> getServicesPage(ProductServicesPageReqVO pageReqVO) {
        return servicesMapper.selectPage(pageReqVO);
    }

}