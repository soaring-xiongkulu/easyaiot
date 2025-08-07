package com.basiclab.iot.device.dal.mysql.product_commands_requests;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_commands_requests.ProductCommandsRequestsDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_commands_requests.vo.*;

/**
 * 产品模型设备下发服务命令属性 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductCommandsRequestsMapper extends BaseMapperX<ProductCommandsRequestsDO> {

    default PageResult<ProductCommandsRequestsDO> selectPage(ProductCommandsRequestsPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductCommandsRequestsDO>()
                .eqIfPresent(ProductCommandsRequestsDO::getServiceId, reqVO.getServiceId())
                .eqIfPresent(ProductCommandsRequestsDO::getCommandsId, reqVO.getCommandsId())
                .eqIfPresent(ProductCommandsRequestsDO::getDatatype, reqVO.getDatatype())
                .eqIfPresent(ProductCommandsRequestsDO::getEnumlist, reqVO.getEnumlist())
                .eqIfPresent(ProductCommandsRequestsDO::getMax, reqVO.getMax())
                .eqIfPresent(ProductCommandsRequestsDO::getMaxlength, reqVO.getMaxlength())
                .eqIfPresent(ProductCommandsRequestsDO::getMin, reqVO.getMin())
                .eqIfPresent(ProductCommandsRequestsDO::getParameterDescription, reqVO.getParameterDescription())
                .likeIfPresent(ProductCommandsRequestsDO::getParameterName, reqVO.getParameterName())
                .eqIfPresent(ProductCommandsRequestsDO::getRequired, reqVO.getRequired())
                .eqIfPresent(ProductCommandsRequestsDO::getStep, reqVO.getStep())
                .eqIfPresent(ProductCommandsRequestsDO::getUnit, reqVO.getUnit())
                .eqIfPresent(ProductCommandsRequestsDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductCommandsRequestsDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductCommandsRequestsDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductCommandsRequestsDO::getId));
    }

}