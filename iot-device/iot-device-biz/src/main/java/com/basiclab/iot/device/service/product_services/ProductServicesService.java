package com.basiclab.iot.device.service.product_services;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product_services.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_services.ProductServicesDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品模型服务 Service 接口
 *
 * @author BasicLab
 */
public interface ProductServicesService {

    /**
     * 创建产品模型服务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createServices(@Valid ProductServicesSaveReqVO createReqVO);

    /**
     * 更新产品模型服务
     *
     * @param updateReqVO 更新信息
     */
    void updateServices(@Valid ProductServicesSaveReqVO updateReqVO);

    /**
     * 删除产品模型服务
     *
     * @param id 编号
     */
    void deleteServices(Long id);

    /**
     * 获得产品模型服务
     *
     * @param id 编号
     * @return 产品模型服务
     */
    ProductServicesDO getServices(Long id);

    /**
     * 获得产品模型服务分页
     *
     * @param pageReqVO 分页查询
     * @return 产品模型服务分页
     */
    PageResult<ProductServicesDO> getServicesPage(ProductServicesPageReqVO pageReqVO);

}