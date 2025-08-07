package com.basiclab.iot.device.service.product;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product.vo.*;
import com.basiclab.iot.device.dal.dataobject.product.Product;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品 Service 接口
 *
 * @author BasicLab
 */
public interface ProductService {

    /**
     * 创建产品
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long create(@Valid ProductSaveReqVO createReqVO);

    /**
     * 查询产品管理
     *
     * @param productIdentification 标识
     * @return 产品管理
     */
    public Product selectByProductIdentification(String productIdentification);


    /**
     * 更新产品
     *
     * @param updateReqVO 更新信息
     */
    void update(@Valid ProductSaveReqVO updateReqVO);

    /**
     * 删除产品
     *
     * @param id 编号
     */
    void delete(Long id);

    /**
     * 获得产品
     *
     * @param id 编号
     * @return 产品
     */
    Product get(Long id);

    /**
     * 获得产品分页
     *
     * @param pageReqVO 分页查询
     * @return 产品分页
     */
    PageResult<Product> getPage(ProductPageReqVO pageReqVO);

}