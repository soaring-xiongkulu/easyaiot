package com.basiclab.iot.device.service.product_type;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product_type.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_type.ProductTypeDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品分类 Service 接口
 *
 * @author BasicLab
 */
public interface ProductTypeService {

    /**
     * 创建产品分类
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createType(@Valid ProductTypeSaveReqVO createReqVO);

    /**
     * 更新产品分类
     *
     * @param updateReqVO 更新信息
     */
    void updateType(@Valid ProductTypeSaveReqVO updateReqVO);

    /**
     * 删除产品分类
     *
     * @param id 编号
     */
    void deleteType(Long id);

    /**
     * 获得产品分类
     *
     * @param id 编号
     * @return 产品分类
     */
    ProductTypeDO getType(Long id);

    /**
     * 获得产品分类分页
     *
     * @param pageReqVO 分页查询
     * @return 产品分类分页
     */
    PageResult<ProductTypeDO> getTypePage(ProductTypePageReqVO pageReqVO);

}