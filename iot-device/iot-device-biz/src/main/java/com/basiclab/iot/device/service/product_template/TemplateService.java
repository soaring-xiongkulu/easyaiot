package com.basiclab.iot.device.service.product_template;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.product_template.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_template.ProductTemplateDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 产品模板 Service 接口
 *
 * @author BasicLab
 */
public interface TemplateService {

    /**
     * 创建产品模板
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createTemplate(@Valid ProductTemplateSaveReqVO createReqVO);

    /**
     * 更新产品模板
     *
     * @param updateReqVO 更新信息
     */
    void updateTemplate(@Valid ProductTemplateSaveReqVO updateReqVO);

    /**
     * 删除产品模板
     *
     * @param id 编号
     */
    void deleteTemplate(Long id);

    /**
     * 获得产品模板
     *
     * @param id 编号
     * @return 产品模板
     */
    ProductTemplateDO getTemplate(Long id);

    /**
     * 获得产品模板分页
     *
     * @param pageReqVO 分页查询
     * @return 产品模板分页
     */
    PageResult<ProductTemplateDO> getTemplatePage(ProductTemplatePageReqVO pageReqVO);

}