package com.basiclab.iot.device.service.app;

import com.basiclab.iot.device.dal.dataobject.AppDO;

import java.util.List;

/**
 * AppService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface AppService {

    /**
     * 根据ID获取应用信息
     *
     * @param id 应用ID
     * @return 应用信息
     */
    AppDO getAppById(Long id);

    /**
     * 根据AppId获取应用信息
     *
     * @param appId 应用ID
     * @return 应用信息
     */
    AppDO getAppByAppId(String appId);

    /**
     * 根据AppKey获取应用信息
     *
     * @param appKey 应用密钥
     * @return 应用信息
     */
    AppDO getAppByAppKey(String appKey);

    /**
     * 根据AppId和AppKey获取应用信息
     *
     * @param appId  应用ID
     * @param appKey 应用密钥
     * @return 应用信息
     */
    AppDO getAppByAppIdAndAppKey(String appId, String appKey);

    /**
     * 获取所有应用列表
     *
     * @return 应用列表
     */
    List<AppDO> getAllApps();

    /**
     * 创建应用
     *
     * @param app 应用信息
     * @return 应用信息
     */
    AppDO createApp(AppDO app);

    /**
     * 更新应用
     *
     * @param app 应用信息
     * @return 是否成功
     */
    boolean updateApp(AppDO app);

    /**
     * 删除应用
     *
     * @param id 应用ID
     * @return 是否成功
     */
    boolean deleteApp(Long id);

    /**
     * 验证AppId、AppKey、AppSecret
     *
     * @param appId     应用ID
     * @param appKey    应用密钥
     * @param appSecret 应用密钥
     * @return 应用信息，验证失败返回null
     */
    AppDO verifyApp(String appId, String appKey, String appSecret);
}

