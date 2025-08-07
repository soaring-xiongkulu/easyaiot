package com.basiclab.iot.device.service.product_template;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_template.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_template.ProductTemplateDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_template.TemplateMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_TEMPLATE_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品模板 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class TemplateServiceImpl implements TemplateService {

    @Resource
    private TemplateMapper templateMapper;

    @Override
    public Long createTemplate(ProductTemplateSaveReqVO createReqVO) {
        // 插入
        ProductTemplateDO template = BeanUtils.toBean(createReqVO, ProductTemplateDO.class);
        templateMapper.insert(template);
        // 返回
        return template.getId();
    }

    @Override
    public void updateTemplate(ProductTemplateSaveReqVO updateReqVO) {
        // 校验存在
        validateTemplateExists(updateReqVO.getId());
        // 更新
        ProductTemplateDO updateObj = BeanUtils.toBean(updateReqVO, ProductTemplateDO.class);
        templateMapper.updateById(updateObj);
    }

    @Override
    public void deleteTemplate(Long id) {
        // 校验存在
        validateTemplateExists(id);
        // 删除
        templateMapper.deleteById(id);
    }

    private void validateTemplateExists(Long id) {
        if (templateMapper.selectById(id) == null) {
            throw exception(PRODUCT_TEMPLATE_NOT_EXISTS);
        }
    }

    @Override
    public ProductTemplateDO getTemplate(Long id) {
        return templateMapper.selectById(id);
    }

    @Override
    public PageResult<ProductTemplateDO> getTemplatePage(ProductTemplatePageReqVO pageReqVO) {
        return templateMapper.selectPage(pageReqVO);
    }

}