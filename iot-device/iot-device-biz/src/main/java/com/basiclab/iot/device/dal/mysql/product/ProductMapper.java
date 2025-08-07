package com.basiclab.iot.device.dal.mysql.product;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product.Product;
import com.basiclab.iot.device.controller.admin.product.vo.*;
import org.apache.ibatis.annotations.Mapper;

/**
 * 产品 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductMapper extends BaseMapperX<Product> {

    default PageResult<Product> selectPage(ProductPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<Product>()
                .eqIfPresent(Product::getTemplateCode, reqVO.getTemplateCode())
                .likeIfPresent(Product::getName, reqVO.getName())
                .eqIfPresent(Product::getPid, reqVO.getPid())
                .likeIfPresent(Product::getManufacturerName, reqVO.getManufacturerName())
                .eqIfPresent(Product::getModel, reqVO.getModel())
                .eqIfPresent(Product::getDataFormat, reqVO.getDataFormat())
                .eqIfPresent(Product::getProtocolType, reqVO.getProtocolType())
                .eqIfPresent(Product::getEnabledStatus, reqVO.getEnabledStatus())
                .eqIfPresent(Product::getRemark, reqVO.getRemark())
                .eqIfPresent(Product::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(Product::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(Product::getUpdateBy, reqVO.getUpdateBy())
                .eqIfPresent(Product::getAuthMode, reqVO.getAuthMode())
                .likeIfPresent(Product::getUserName, reqVO.getUserName())
                .eqIfPresent(Product::getPassword, reqVO.getPassword())
                .eqIfPresent(Product::getConnector, reqVO.getConnector())
                .eqIfPresent(Product::getSignKey, reqVO.getSignKey())
                .eqIfPresent(Product::getEncryptMethod, reqVO.getEncryptMethod())
                .eqIfPresent(Product::getEncryptKey, reqVO.getEncryptKey())
                .eqIfPresent(Product::getEncryptVector, reqVO.getEncryptVector())
                .eqIfPresent(Product::getProductTypeId, reqVO.getProductTypeId())
                .likeIfPresent(Product::getProductTypeName, reqVO.getProductTypeName())
                .eqIfPresent(Product::getManufacturerCode, reqVO.getManufacturerCode())
                .orderByDesc(Product::getId));
    }

}