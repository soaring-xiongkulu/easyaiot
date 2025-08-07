package com.basiclab.iot.device.dal.mysql.product_services;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_services.ProductServicesDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_services.vo.*;

/**
 * 产品模型服务 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductServicesMapper extends BaseMapperX<ProductServicesDO> {

    default PageResult<ProductServicesDO> selectPage(ProductServicesPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductServicesDO>()
                .eqIfPresent(ProductServicesDO::getServiceCode, reqVO.getServiceCode())
                .likeIfPresent(ProductServicesDO::getServiceName, reqVO.getServiceName())
                .eqIfPresent(ProductServicesDO::getTemplateCode, reqVO.getTemplateCode())
                .eqIfPresent(ProductServicesDO::getPid, reqVO.getPid())
                .eqIfPresent(ProductServicesDO::getStatus, reqVO.getStatus())
                .eqIfPresent(ProductServicesDO::getDescription, reqVO.getDescription())
                .eqIfPresent(ProductServicesDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductServicesDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductServicesDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductServicesDO::getId));
    }

}