package com.basiclab.iot.device.service.product_properties;

import javax.validation.*;

import com.basiclab.iot.device.controller.admin.product.ProductProperties;
import com.basiclab.iot.device.controller.admin.product_properties.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_properties.ProductPropertiesDO;
import com.basiclab.iot.common.domain.PageResult;

import java.util.List;

/**
 * 产品模型属性 Service 接口
 *
 * @author BasicLab
 */
public interface ProductPropertiesService {

    ProductProperties selectByPrimaryKey(Long id);

    Boolean checkPropertyCode(String identification, String propertyCode, Integer flag);

    ProductProperties selectProductPropertiesById(Long id);

    List<ProductProperties> selectProductPropertiesList(ProductProperties productProperties);

    int insertProductProperties(ProductProperties productProperties);

    Long createProperties(@Valid ProductPropertiesSaveReqVO createReqVO);

    void updateProperties(@Valid ProductPropertiesSaveReqVO updateReqVO);

    void deleteProperties(Long id);

    ProductPropertiesDO getProperties(Long id);

    PageResult<ProductPropertiesDO> getPropertiesPage(ProductPropertiesPageReqVO pageReqVO);
}