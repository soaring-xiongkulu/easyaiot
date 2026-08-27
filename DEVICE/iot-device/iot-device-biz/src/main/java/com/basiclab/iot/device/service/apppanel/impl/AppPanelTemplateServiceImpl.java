package com.basiclab.iot.device.service.apppanel.impl;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.util.StrUtil;
import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.device.dal.dataobject.AppPanelTemplateDO;
import com.basiclab.iot.device.dal.pgsql.apppanel.AppPanelTemplateMapper;
import com.basiclab.iot.device.service.apppanel.AppPanelTemplateService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.List;

/**
 * AppPanelTemplateServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class AppPanelTemplateServiceImpl implements AppPanelTemplateService {

    @Resource
    private AppPanelTemplateMapper appPanelTemplateMapper;

    @Override
    public List<AppPanelTemplateDO> selectList(LambdaQueryWrapper<AppPanelTemplateDO> wrapper) {
        return appPanelTemplateMapper.selectList(wrapper);
    }

    @Override
    public AppPanelTemplateDO getAppPanelTemplate(Long id) {
        return appPanelTemplateMapper.selectById(id);
    }

    @Override
    public List<AppPanelTemplateDO> getAllList() {
        LambdaQueryWrapper<AppPanelTemplateDO> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(AppPanelTemplateDO::getUpdatedTime);
        return appPanelTemplateMapper.selectList(wrapper);
    }

    @Override
    public AppPanelTemplateDO createAppPanelTemplate(AppPanelTemplateDO template) {
        validate(template, true);
        template.setId(null);
        if (StrUtil.isBlank(template.getStatus())) {
            template.setStatus(AppPanelTemplateDO.STATUS_DRAFT);
        }
        if (template.getVersion() == null) {
            template.setVersion(1);
        }
        appPanelTemplateMapper.insert(template);
        return template;
    }

    @Override
    public boolean updateAppPanelTemplate(AppPanelTemplateDO template) {
        Assert.notNull(template.getId(), "模板ID不能为空");
        AppPanelTemplateDO exists = appPanelTemplateMapper.selectById(template.getId());
        Assert.notNull(exists, "模板不存在");
        validate(template, false);
        // 编码与版本号不允许直接改：编码是引用键，版本只随发布递增
        template.setTemplateCode(null);
        template.setVersion(null);
        return appPanelTemplateMapper.updateById(template) > 0;
    }

    @Override
    public boolean deleteAppPanelTemplate(Long id) {
        Assert.notNull(id, "模板ID不能为空");
        return appPanelTemplateMapper.deleteById(id) > 0;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppPanelTemplateDO publishAppPanelTemplate(Long id) {
        AppPanelTemplateDO template = appPanelTemplateMapper.selectById(id);
        Assert.notNull(template, "模板不存在");
        validateSchemaJson(template.getPanelSchema());

        // 同产品其他已发布模板先下线，保证一个产品只有一个生效模板
        AppPanelTemplateDO offline = new AppPanelTemplateDO();
        offline.setStatus(AppPanelTemplateDO.STATUS_DISABLED);
        LambdaQueryWrapper<AppPanelTemplateDO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AppPanelTemplateDO::getProductIdentification, template.getProductIdentification())
                .eq(AppPanelTemplateDO::getStatus, AppPanelTemplateDO.STATUS_PUBLISHED)
                .ne(AppPanelTemplateDO::getId, id);
        appPanelTemplateMapper.update(offline, wrapper);

        AppPanelTemplateDO publish = new AppPanelTemplateDO();
        publish.setId(id);
        publish.setStatus(AppPanelTemplateDO.STATUS_PUBLISHED);
        publish.setVersion((template.getVersion() == null ? 0 : template.getVersion()) + 1);
        appPanelTemplateMapper.updateById(publish);

        return appPanelTemplateMapper.selectById(id);
    }

    @Override
    public AppPanelTemplateDO unpublishAppPanelTemplate(Long id) {
        AppPanelTemplateDO update = new AppPanelTemplateDO();
        update.setId(id);
        update.setStatus(AppPanelTemplateDO.STATUS_DISABLED);
        appPanelTemplateMapper.updateById(update);
        return appPanelTemplateMapper.selectById(id);
    }

    @Override
    public AppPanelTemplateDO getPublishedByProductIdentification(String productIdentification) {
        if (StrUtil.isBlank(productIdentification)) {
            return null;
        }
        return appPanelTemplateMapper.selectPublishedByProductIdentification(productIdentification);
    }

    private void validate(AppPanelTemplateDO template, boolean create) {
        Assert.notNull(template, "模板信息不能为空");
        Assert.notBlank(template.getTemplateName(), "模板名称不能为空");
        if (create) {
            Assert.notBlank(template.getTemplateCode(), "模板编码不能为空");
            AppPanelTemplateDO byCode = appPanelTemplateMapper.selectByTemplateCode(template.getTemplateCode());
            Assert.isNull(byCode, "模板编码已存在: " + template.getTemplateCode());
            // 同一产品同时只能绑定一个未停用模板（草稿或已发布），避免下发歧义
            checkProductBoundOnce(template.getProductIdentification(), null);
        } else {
            checkProductBoundOnce(template.getProductIdentification(), template.getId());
        }
        if (StrUtil.isNotBlank(template.getPanelSchema())) {
            validateSchemaJson(template.getPanelSchema());
        }
    }

    private void checkProductBoundOnce(String productIdentification, Long excludeId) {
        if (StrUtil.isBlank(productIdentification)) {
            return;
        }
        LambdaQueryWrapper<AppPanelTemplateDO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AppPanelTemplateDO::getProductIdentification, productIdentification)
                .in(AppPanelTemplateDO::getStatus, AppPanelTemplateDO.STATUS_DRAFT, AppPanelTemplateDO.STATUS_PUBLISHED)
                .ne(excludeId != null, AppPanelTemplateDO::getId, excludeId);
        Long count = appPanelTemplateMapper.selectCount(wrapper);
        Assert.isTrue(count == null || count == 0, "该产品已绑定其他面板模板，请先解绑或停用原模板");
    }

    private void validateSchemaJson(String panelSchema) {
        try {
            JSON.parse(panelSchema);
        } catch (Exception e) {
            throw new IllegalArgumentException("面板模板 JSON 格式不合法：" + e.getMessage());
        }
    }
}
