package com.basiclab.iot.device.service.apppanel;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.device.dal.dataobject.AppPanelTemplateDO;

import java.util.List;

/**
 * AppPanelTemplateService
 *
 * App 控制面板模板：云端定制每个产品在 APP 内展示的控制页面
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface AppPanelTemplateService {

    /**
     * 条件查询列表（配合 PageHelper 分页使用）
     *
     * @param wrapper 查询条件
     * @return 列表
     */
    List<AppPanelTemplateDO> selectList(LambdaQueryWrapper<AppPanelTemplateDO> wrapper);

    /**
     * 按 ID 查询
     *
     * @param id 主键
     * @return 模板
     */
    AppPanelTemplateDO getAppPanelTemplate(Long id);

    /**
     * 全部模板（下拉选择等场景）
     *
     * @return 列表
     */
    List<AppPanelTemplateDO> getAllList();

    /**
     * 创建模板
     *
     * @param template 模板
     * @return 保存后的模板
     */
    AppPanelTemplateDO createAppPanelTemplate(AppPanelTemplateDO template);

    /**
     * 更新模板
     *
     * @param template 模板
     * @return 是否成功
     */
    boolean updateAppPanelTemplate(AppPanelTemplateDO template);

    /**
     * 删除模板
     *
     * @param id 主键
     * @return 是否成功
     */
    boolean deleteAppPanelTemplate(Long id);

    /**
     * 发布模板：状态置为 PUBLISHED，版本号自增，并将同产品其他已发布模板下线
     *
     * @param id 主键
     * @return 发布后的模板
     */
    AppPanelTemplateDO publishAppPanelTemplate(Long id);

    /**
     * 停用模板
     *
     * @param id 主键
     * @return 停用后的模板
     */
    AppPanelTemplateDO unpublishAppPanelTemplate(Long id);

    /**
     * 按产品标识取当前生效（已发布）的模板 —— APP 下发入口
     *
     * @param productIdentification 产品标识
     * @return 已发布模板；未配置返回 null
     */
    AppPanelTemplateDO getPublishedByProductIdentification(String productIdentification);
}
