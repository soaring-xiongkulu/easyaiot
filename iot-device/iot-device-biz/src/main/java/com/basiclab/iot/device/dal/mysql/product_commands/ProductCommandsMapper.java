package com.basiclab.iot.device.dal.mysql.product_commands;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_commands.ProductCommandsDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_commands.vo.*;

/**
 * 产品模型设备服务命令 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProductCommandsMapper extends BaseMapperX<ProductCommandsDO> {

    default PageResult<ProductCommandsDO> selectPage(ProductCommandsPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductCommandsDO>()
                .eqIfPresent(ProductCommandsDO::getServiceId, reqVO.getServiceId())
                .likeIfPresent(ProductCommandsDO::getName, reqVO.getName())
                .eqIfPresent(ProductCommandsDO::getDescription, reqVO.getDescription())
                .eqIfPresent(ProductCommandsDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductCommandsDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductCommandsDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductCommandsDO::getId));
    }

}