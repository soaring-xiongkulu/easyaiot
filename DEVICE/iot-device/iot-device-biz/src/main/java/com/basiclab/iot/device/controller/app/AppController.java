package com.basiclab.iot.device.controller.app;

import cn.hutool.core.bean.BeanUtil;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.dal.dataobject.AppDO;
import com.basiclab.iot.device.domain.app.vo.App;
import com.basiclab.iot.device.service.app.AppService;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

/**
 * AppController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "应用密钥管理")
@RestController
@RequestMapping("/app")
@Validated
@Slf4j
public class AppController extends BaseController {

    @Resource
    private AppService appService;

    @PostMapping("/create")
    @ApiOperation("创建应用密钥")
    public AjaxResult createApp(@RequestBody AppDO app) {
        try {
            AppDO result = appService.createApp(app);
            return AjaxResult.success(result);
        } catch (Exception e) {
            log.error("[createApp][创建应用密钥失败]", e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @PutMapping("/update")
    @ApiOperation("更新应用密钥")
    public AjaxResult updateApp(@RequestBody AppDO app) {
        try {
            boolean result = appService.updateApp(app);
            return toAjax(result ? 1 : 0);
        } catch (Exception e) {
            log.error("[updateApp][更新应用密钥失败]", e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @DeleteMapping("/delete")
    @ApiOperation("删除应用密钥")
    @Parameter(name = "id", description = "应用ID", required = true)
    public AjaxResult deleteApp(@RequestParam("id") Long id) {
        try {
            boolean result = appService.deleteApp(id);
            return toAjax(result ? 1 : 0);
        } catch (Exception e) {
            log.error("[deleteApp][删除应用密钥失败]", e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @GetMapping("/get")
    @ApiOperation("获取应用密钥")
    @Parameter(name = "id", description = "应用ID", required = true, example = "1")
    public AjaxResult getApp(@RequestParam("id") Long id) {
        try {
            AppDO app = appService.getAppById(id);
            return AjaxResult.success(app);
        } catch (Exception e) {
            log.error("[getApp][获取应用密钥失败]", e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @GetMapping("/get-by-app-id")
    @ApiOperation("根据AppId获取应用密钥")
    @Parameter(name = "appId", description = "应用ID", required = true)
    public R<App> getAppByAppId(@RequestParam("appId") String appId) {
        try {
            AppDO appDO = appService.getAppByAppId(appId);
            if (appDO == null) {
                return R.fail("应用不存在");
            }
            App app = BeanUtil.copyProperties(appDO, App.class);
            return R.ok(app);
        } catch (Exception e) {
            log.error("[getAppByAppId][获取应用密钥失败]", e);
            return R.fail(e.getMessage());
        }
    }

    @GetMapping("/list")
    @ApiOperation("获取所有应用密钥列表")
    public AjaxResult getAllApps() {
        try {
            List<AppDO> apps = appService.getAllApps();
            return AjaxResult.success(apps);
        } catch (Exception e) {
            log.error("[getAllApps][获取应用密钥列表失败]", e);
            return AjaxResult.error(e.getMessage());
        }
    }

    @PostMapping("/verify")
    @ApiOperation("验证AppId、AppKey、AppSecret")
    public R<App> verifyApp(@RequestParam("appId") String appId,
                             @RequestParam("appKey") String appKey,
                             @RequestParam("appSecret") String appSecret) {
        try {
            AppDO appDO = appService.verifyApp(appId, appKey, appSecret);
            if (appDO != null) {
                App app = BeanUtil.copyProperties(appDO, App.class);
                return R.ok(app);
            } else {
                return R.fail("验证失败");
            }
        } catch (Exception e) {
            log.error("[verifyApp][验证应用密钥失败]", e);
            return R.fail(e.getMessage());
        }
    }
}

