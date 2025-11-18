package com.basiclab.iot.sink.auth.service;

import com.basiclab.iot.device.domain.app.vo.App;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.sink.auth.dto.RegisterResp;
import com.basiclab.iot.sink.auth.enums.SignMethod;

/**
 * DeviceRegisterService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface DeviceRegisterService {

    /**
     * 根据产品标识获取产品信息
     *
     * @param productKey 产品标识
     * @return 产品信息
     */
    Product getProductByProductKey(String productKey);

    /**
     * 验证AppId、AppKey、AppSecret（直接查询数据库表）
     *
     * @param appId     应用ID
     * @param appKey    应用密钥
     * @param appSecret 应用密钥
     * @return 应用信息，验证失败返回null
     */
    App verifyApp(String appId, String appKey, String appSecret);

    /**
     * 验证签名（使用common-utils中的SignUtils）
     *
     * @param signMethod   签名方法
     * @param content      待签名内容
     * @param secret       密钥（使用AppSecret）
     * @param sign         签名
     * @return 验证结果
     */
    boolean verifySign(SignMethod signMethod, String content, String secret, String sign);

    /**
     * 注册设备
     *
     * @param product       产品信息
     * @param productKey    产品标识
     * @param uniqueNo      设备唯一标识
     * @param deviceName    设备名称
     * @param deviceDesc    设备描述
     * @return 设备信息
     */
    Device registerDevice(Product product, String productKey, String uniqueNo, String deviceName, String deviceDesc);

    /**
     * 构建注册响应
     *
     * @param productIdentification    产品标识
     * @param deviceIdentification    设备标识
     * @param deviceSecret  设备密钥
     * @return 注册响应
     */
    RegisterResp buildRegisterResp(String productIdentification, String deviceIdentification, String deviceSecret);
}

