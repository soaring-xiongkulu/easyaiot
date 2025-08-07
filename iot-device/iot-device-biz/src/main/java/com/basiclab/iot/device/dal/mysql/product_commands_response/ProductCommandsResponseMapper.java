package com.basiclab.iot.device.dal.mysql.product_commands_response;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_commands_response.ProductCommandsResponseDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_commands_response.vo.*;

/**
 * 产品模型设备响应服务命令属性 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductCommandsResponseMapper extends BaseMapperX<ProductCommandsResponseDO> {

    default PageResult<ProductCommandsResponseDO> selectPage(ProductCommandsResponsePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductCommandsResponseDO>()
                .eqIfPresent(ProductCommandsResponseDO::getCommandsId, reqVO.getCommandsId())
                .eqIfPresent(ProductCommandsResponseDO::getServiceId, reqVO.getServiceId())
                .eqIfPresent(ProductCommandsResponseDO::getDatatype, reqVO.getDatatype())
                .eqIfPresent(ProductCommandsResponseDO::getEnumlist, reqVO.getEnumlist())
                .eqIfPresent(ProductCommandsResponseDO::getMax, reqVO.getMax())
                .eqIfPresent(ProductCommandsResponseDO::getMaxlength, reqVO.getMaxlength())
                .eqIfPresent(ProductCommandsResponseDO::getMin, reqVO.getMin())
                .eqIfPresent(ProductCommandsResponseDO::getParameterDescription, reqVO.getParameterDescription())
                .likeIfPresent(ProductCommandsResponseDO::getParameterName, reqVO.getParameterName())
                .eqIfPresent(ProductCommandsResponseDO::getRequired, reqVO.getRequired())
                .eqIfPresent(ProductCommandsResponseDO::getStep, reqVO.getStep())
                .eqIfPresent(ProductCommandsResponseDO::getUnit, reqVO.getUnit())
                .eqIfPresent(ProductCommandsResponseDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductCommandsResponseDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductCommandsResponseDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductCommandsResponseDO::getId));
    }

}