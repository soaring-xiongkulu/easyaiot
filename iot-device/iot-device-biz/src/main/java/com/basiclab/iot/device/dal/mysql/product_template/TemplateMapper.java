package com.basiclab.iot.device.dal.mysql.product_template;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.device.dal.dataobject.product_template.ProductTemplateDO;
import org.apache.ibatis.annotations.Mapper;
import com.basiclab.iot.device.controller.admin.product_template.vo.*;

/**
 * 产品模板 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface TemplateMapper extends BaseMapperX<ProductTemplateDO> {

    default PageResult<ProductTemplateDO> selectPage(ProductTemplatePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProductTemplateDO>()
                .eqIfPresent(ProductTemplateDO::getAppId, reqVO.getAppId())
                .eqIfPresent(ProductTemplateDO::getTemplateCode, reqVO.getTemplateCode())
                .likeIfPresent(ProductTemplateDO::getTemplateName, reqVO.getTemplateName())
                .eqIfPresent(ProductTemplateDO::getStatus, reqVO.getStatus())
                .eqIfPresent(ProductTemplateDO::getRemark, reqVO.getRemark())
                .eqIfPresent(ProductTemplateDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProductTemplateDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProductTemplateDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(ProductTemplateDO::getId));
    }

}