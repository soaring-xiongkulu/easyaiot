package com.basiclab.iot.device.service.app.impl;

import cn.hutool.core.lang.Assert;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.device.dal.dataobject.AppDO;
import com.basiclab.iot.device.dal.pgsql.app.AppMapper;
import com.basiclab.iot.device.service.app.AppService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;

/**
 * AppServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class AppServiceImpl implements AppService {

    @Resource
    private AppMapper appMapper;

    @Override
    public AppDO getAppById(Long id) {
        return appMapper.selectById(id);
    }

    @Override
    public AppDO getAppByAppId(String appId) {
        return appMapper.selectByAppId(appId);
    }

    @Override
    public AppDO getAppByAppKey(String appKey) {
        return appMapper.selectByAppKey(appKey);
    }

    @Override
    public AppDO getAppByAppIdAndAppKey(String appId, String appKey) {
        return appMapper.selectByAppIdAndAppKey(appId, appKey);
    }

    @Override
    public List<AppDO> getAllApps() {
        LambdaQueryWrapper<AppDO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AppDO::getDeleted, 0);
        wrapper.orderByDesc(AppDO::getCreatedTime);
        return appMapper.selectList(wrapper);
    }

    @Override
    public AppDO createApp(AppDO app) {
        Assert.notNull(app, "应用信息不能为空");
        Assert.notBlank(app.getAppId(), "应用ID不能为空");
        Assert.notBlank(app.getAppKey(), "应用密钥不能为空");
        Assert.notBlank(app.getAppSecret(), "应用密钥不能为空");

        // 检查AppId是否已存在
        AppDO existingApp = appMapper.selectByAppId(app.getAppId());
        if (existingApp != null) {
            throw new RuntimeException("应用ID已存在: " + app.getAppId());
        }

        // 检查AppKey是否已存在
        existingApp = appMapper.selectByAppKey(app.getAppKey());
        if (existingApp != null) {
            throw new RuntimeException("应用密钥已存在: " + app.getAppKey());
        }

        // 设置默认值
        if (!StringUtils.hasText(app.getStatus())) {
            app.setStatus("ENABLE");
        }
        if (!StringUtils.hasText(app.getPermissionType())) {
            app.setPermissionType("READ_WRITE");
        }
        if (app.getCreatedTime() == null) {
            app.setCreatedTime(LocalDateTime.now());
        }
        if (!StringUtils.hasText(app.getCreatedBy())) {
            app.setCreatedBy("system");
        }

        appMapper.insert(app);
        log.info("[createApp][应用创建成功，appId: {}, appKey: {}]", app.getAppId(), app.getAppKey());
        return app;
    }

    @Override
    public boolean updateApp(AppDO app) {
        Assert.notNull(app, "应用信息不能为空");
        Assert.notNull(app.getId(), "应用ID不能为空");

        AppDO existingApp = appMapper.selectById(app.getId());
        if (existingApp == null) {
            throw new RuntimeException("应用不存在: " + app.getId());
        }

        app.setUpdatedTime(LocalDateTime.now());
        if (!StringUtils.hasText(app.getUpdatedBy())) {
            app.setUpdatedBy("system");
        }

        int result = appMapper.updateById(app);
        log.info("[updateApp][应用更新成功，appId: {}]", app.getAppId());
        return result > 0;
    }

    @Override
    public boolean deleteApp(Long id) {
        Assert.notNull(id, "应用ID不能为空");
        int result = appMapper.deleteById(id);
        log.info("[deleteApp][应用删除成功，id: {}]", id);
        return result > 0;
    }

    @Override
    public AppDO verifyApp(String appId, String appKey, String appSecret) {
        if (!StringUtils.hasText(appId) || !StringUtils.hasText(appKey) || !StringUtils.hasText(appSecret)) {
            return null;
        }

        AppDO app = appMapper.selectByAppIdAndAppKey(appId, appKey);
        if (app == null) {
            log.warn("[verifyApp][应用不存在，appId: {}, appKey: {}]", appId, appKey);
            return null;
        }

        // 检查状态
        if (!"ENABLE".equals(app.getStatus())) {
            log.warn("[verifyApp][应用已禁用，appId: {}, appKey: {}]", appId, appKey);
            return null;
        }

        // 检查过期时间
        if (app.getExpireTime() != null && app.getExpireTime().isBefore(LocalDateTime.now())) {
            log.warn("[verifyApp][应用已过期，appId: {}, appKey: {}, expireTime: {}]", appId, appKey, app.getExpireTime());
            return null;
        }

        // 验证AppSecret
        if (!appSecret.equals(app.getAppSecret())) {
            log.warn("[verifyApp][应用密钥错误，appId: {}, appKey: {}]", appId, appKey);
            return null;
        }

        log.info("[verifyApp][应用验证成功，appId: {}, appKey: {}]", appId, appKey);
        return app;
    }
}

