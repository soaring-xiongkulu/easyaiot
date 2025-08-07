package com.basiclab.iot.device.dal.mysql.product_event;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_event.ProductEventDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_event.vo.*;

/**
 * 产品模型事件 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductEventMapper extends BaseMapperX<ProductEventDO> {

    default PageResult<ProductEventDO> selectPage(ProductEventPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductEventDO>()
                .likeIfPresent(ProductEventDO::getEventName, reqVO.getEventName())
                .eqIfPresent(ProductEventDO::getEventCode, reqVO.getEventCode())
                .eqIfPresent(ProductEventDO::getEventType, reqVO.getEventType())
                .eqIfPresent(ProductEventDO::getTemplateCode, reqVO.getTemplateCode())
                .eqIfPresent(ProductEventDO::getPid, reqVO.getPid())
                .eqIfPresent(ProductEventDO::getEnabledStatus, reqVO.getEnabledStatus())
                .eqIfPresent(ProductEventDO::getDescription, reqVO.getDescription())
                .eqIfPresent(ProductEventDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductEventDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductEventDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductEventDO::getId));
    }

}