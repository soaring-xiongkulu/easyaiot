package com.basiclab.iot.device.controller.apppanel;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.utils.StringUtils;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.dal.dataobject.AppPanelTemplateDO;
import com.basiclab.iot.device.service.apppanel.AppPanelTemplateService;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * AppPanelTemplateController
 *
 * App 控制面板模板管理：云端定制每个产品在 APP 内展示的控制页面，
 * 模板绑定产品并发布后，APP 端通过 get-by-product 接口拉取并动态渲染控制页。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "App控制面板模板")
@RestController
@RequestMapping("/appPanelTemplate")
@Slf4j
public class AppPanelTemplateController extends BaseController {

    @Resource
    private AppPanelTemplateService appPanelTemplateService;

    @PostMapping("/create")
    @ApiOperation("创建App面板模板")
    public AjaxResult create(@RequestBody AppPanelTemplateDO template) {
        try {
            return AjaxResult.success(appPanelTemplateService.createAppPanelTemplate(template));
        } catch (Exception e) {
            log.error("[create][创建App面板模板({})失败]", template, e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @PutMapping("/update")
    @ApiOperation("更新App面板模板")
    public AjaxResult update(@RequestBody AppPanelTemplateDO template) {
        try {
            return toAjax(appPanelTemplateService.updateAppPanelTemplate(template) ? 1 : 0);
        } catch (Exception e) {
            log.error("[update][更新App面板模板({})失败]", template, e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @DeleteMapping("/delete")
    @ApiOperation("删除App面板模板")
    @Parameter(name = "id", description = "模板ID", required = true)
    public AjaxResult delete(@RequestParam("id") Long id) {
        try {
            return toAjax(appPanelTemplateService.deleteAppPanelTemplate(id) ? 1 : 0);
        } catch (Exception e) {
            log.error("[delete][删除App面板模板({})失败]", id, e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @GetMapping("/get")
    @ApiOperation("获取App面板模板详情")
    @Parameter(name = "id", description = "模板ID", required = true, example = "1")
    public AjaxResult get(@RequestParam("id") Long id) {
        return AjaxResult.success(appPanelTemplateService.getAppPanelTemplate(id));
    }

    @GetMapping("/page")
    @ApiOperation("分页查询App面板模板")
    public TableDataInfo page(@RequestParam(value = "templateName", required = false) String templateName,
                              @RequestParam(value = "productIdentification", required = false) String productIdentification,
                              @RequestParam(value = "status", required = false) String status) {
        startPage();
        LambdaQueryWrapper<AppPanelTemplateDO> wrapper = new LambdaQueryWrapper<>();
        wrapper.like(StringUtils.isNotEmpty(templateName), AppPanelTemplateDO::getTemplateName, templateName)
                .eq(StringUtils.isNotEmpty(productIdentification), AppPanelTemplateDO::getProductIdentification, productIdentification)
                .eq(StringUtils.isNotEmpty(status), AppPanelTemplateDO::getStatus, status)
                .orderByDesc(AppPanelTemplateDO::getUpdatedTime);
        List<AppPanelTemplateDO> list = appPanelTemplateService.selectList(wrapper);
        return getDataTable(list);
    }

    @GetMapping("/list")
    @ApiOperation("全部App面板模板")
    public AjaxResult list() {
        return AjaxResult.success(appPanelTemplateService.getAllList());
    }

    @PutMapping("/publish")
    @ApiOperation("发布App面板模板（版本号自增，同产品其他已发布模板自动下线）")
    @Parameter(name = "id", description = "模板ID", required = true)
    public AjaxResult publish(@RequestParam("id") Long id) {
        try {
            return AjaxResult.success(appPanelTemplateService.publishAppPanelTemplate(id));
        } catch (Exception e) {
            log.error("[publish][发布App面板模板({})失败]", id, e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @PutMapping("/unpublish")
    @ApiOperation("停用App面板模板")
    @Parameter(name = "id", description = "模板ID", required = true)
    public AjaxResult unpublish(@RequestParam("id") Long id) {
        try {
            return AjaxResult.success(appPanelTemplateService.unpublishAppPanelTemplate(id));
        } catch (Exception e) {
            log.error("[unpublish][停用App面板模板({})失败]", id, e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @GetMapping("/get-by-product")
    @ApiOperation("按产品标识取当前生效的面板模板（APP下发入口）")
    @Parameter(name = "productIdentification", description = "产品标识", required = true)
    public R<AppPanelTemplateDO> getByProduct(@RequestParam("productIdentification") String productIdentification) {
        return R.ok(appPanelTemplateService.getPublishedByProductIdentification(productIdentification));
    }
}
