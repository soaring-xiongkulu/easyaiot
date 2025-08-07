package com.basiclab.iot.device.dal.mysql.product_event_response;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_event_response.ProductEventResponseDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_event_response.vo.*;

/**
 * 产品模型事件响应 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductEventResponseMapper extends BaseMapperX<ProductEventResponseDO> {

    default PageResult<ProductEventResponseDO> selectPage(ProductEventResponsePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductEventResponseDO>()
                .eqIfPresent(ProductEventResponseDO::getEventId, reqVO.getEventId())
                .eqIfPresent(ProductEventResponseDO::getServiceId, reqVO.getServiceId())
                .eqIfPresent(ProductEventResponseDO::getDatatype, reqVO.getDatatype())
                .eqIfPresent(ProductEventResponseDO::getEnumlist, reqVO.getEnumlist())
                .eqIfPresent(ProductEventResponseDO::getMax, reqVO.getMax())
                .eqIfPresent(ProductEventResponseDO::getMaxlength, reqVO.getMaxlength())
                .eqIfPresent(ProductEventResponseDO::getMin, reqVO.getMin())
                .eqIfPresent(ProductEventResponseDO::getParameterDescription, reqVO.getParameterDescription())
                .likeIfPresent(ProductEventResponseDO::getParameterName, reqVO.getParameterName())
                .eqIfPresent(ProductEventResponseDO::getRequired, reqVO.getRequired())
                .eqIfPresent(ProductEventResponseDO::getStep, reqVO.getStep())
                .eqIfPresent(ProductEventResponseDO::getUnit, reqVO.getUnit())
                .eqIfPresent(ProductEventResponseDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductEventResponseDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductEventResponseDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductEventResponseDO::getId));
    }

}