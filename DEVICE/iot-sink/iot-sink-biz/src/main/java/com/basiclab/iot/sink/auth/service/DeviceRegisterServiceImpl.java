package com.basiclab.iot.sink.auth.service;

import com.basiclab.iot.device.RemoteDeviceService;
import com.basiclab.iot.device.RemoteProductService;
import com.basiclab.iot.device.domain.app.vo.App;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.utils.SignUtils;
import com.basiclab.iot.sink.auth.dto.RegisterResp;
import com.basiclab.iot.sink.auth.enums.SignMethod;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.dal.dataobject.AppDO;
import com.basiclab.iot.sink.dal.mapper.AppMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

import javax.annotation.Resource;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.sink.enums.ErrorCodeConstants.DEVICE_AUTH_FAIL;

/**
 * DeviceRegisterServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
@Slf4j
public class DeviceRegisterServiceImpl implements DeviceRegisterService {

    @Resource
    private RemoteProductService remoteProductService;

    @Resource
    private RemoteDeviceService remoteDeviceService;

    @Resource
    private IotGatewayProperties gatewayProperties;

    @Resource
    private RestTemplate restTemplate;

    @Resource
    private AppMapper appMapper;

    /**
     * 根据产品标识获取产品信息
     *
     * @param productKey 产品标识
     * @return 产品信息
     */
    @Override
    public Product getProductByProductKey(String productKey) {
        R<Product> result = remoteProductService.selectByProductIdentification(productKey);
        if (result == null || result.getCode() != R.SUCCESS || result.getData() == null) {
            log.warn("[getProductByProductKey][产品不存在，productKey: {}]", productKey);
            return null;
        }
        return result.getData();
    }

    /**
     * 验证AppId、AppKey、AppSecret（直接查询数据库表）
     *
     * @param appId     应用ID
     * @param appKey    应用密钥
     * @param appSecret 应用密钥
     * @return 应用信息，验证失败返回null
     */
    @Override
    public App verifyApp(String appId, String appKey, String appSecret) {
        if (!StringUtils.hasText(appId) || !StringUtils.hasText(appKey) || !StringUtils.hasText(appSecret)) {
            return null;
        }

        AppDO appDO = appMapper.selectByAppIdAndAppKey(appId, appKey);
        if (appDO == null) {
            log.warn("[verifyApp][应用不存在，appId: {}, appKey: {}]", appId, appKey);
            return null;
        }

        // 检查状态
        if (!"ENABLE".equals(appDO.getStatus())) {
            log.warn("[verifyApp][应用已禁用，appId: {}, appKey: {}]", appId, appKey);
            return null;
        }

        // 检查过期时间
        if (appDO.getExpireTime() != null && appDO.getExpireTime().isBefore(LocalDateTime.now())) {
            log.warn("[verifyApp][应用已过期，appId: {}, appKey: {}, expireTime: {}]", appId, appKey, appDO.getExpireTime());
            return null;
        }

        // 验证AppSecret
        if (!appSecret.equals(appDO.getAppSecret())) {
            log.warn("[verifyApp][应用密钥错误，appId: {}, appKey: {}]", appId, appKey);
            return null;
        }

        log.info("[verifyApp][应用验证成功，appId: {}, appKey: {}]", appId, appKey);
        
        // 将 AppDO 转换为 App VO
        App app = convertToApp(appDO);
        return app;
    }

    /**
     * 将 AppDO 转换为 App VO
     *
     * @param appDO 应用 DO
     * @return 应用 VO
     */
    private App convertToApp(AppDO appDO) {
        if (appDO == null) {
            return null;
        }
        App app = new App();
        BeanUtils.copyProperties(appDO, app);
        // BaseEntity2 的字段映射到 BaseEntity
        app.setCreateBy(appDO.getCreatedBy());
        app.setCreateTime(appDO.getCreatedTime());
        app.setUpdateBy(appDO.getUpdatedBy());
        app.setUpdateTime(appDO.getUpdatedTime());
        return app;
    }

    /**
     * 验证签名（使用common-utils中的SignUtils）
     *
     * @param signMethod   签名方法
     * @param content      待签名内容
     * @param secret       密钥（使用AppSecret）
     * @param sign         签名
     * @return 验证结果
     */
    @Override
    public boolean verifySign(SignMethod signMethod, String content, String secret, String sign) {
        if (signMethod == null) {
            return false;
        }
        SignUtils.SignMethod utilsSignMethod = SignUtils.SignMethod.get(signMethod.getMethod());
        if (utilsSignMethod == null) {
            return false;
        }
        return SignUtils.verify(content, secret, sign, utilsSignMethod);
    }

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
    @Override
    public Device registerDevice(Product product, String productKey, String uniqueNo, String deviceName, String deviceDesc) {
        // 检查设备是否已存在
        R<Device> deviceResult = remoteDeviceService.selectByProductIdentificationAndDeviceIdentification(
                productKey, uniqueNo);
        if (deviceResult != null && deviceResult.getCode() == R.SUCCESS && deviceResult.getData() != null) {
            // 设备已存在，直接返回
            log.info("[registerDevice][设备已存在，productKey: {}, uniqueNo: {}]", productKey, uniqueNo);
            return deviceResult.getData();
        }

        // 创建设备
        Device device = new Device();
        device.setProductIdentification(productKey);
        device.setDeviceIdentification(uniqueNo);
        if (StringUtils.hasText(deviceName)) {
            device.setDeviceName(deviceName);
        } else {
            device.setDeviceName(product.getProductName() + "-" + uniqueNo.substring(Math.max(0, uniqueNo.length() - 4)));
        }
        if (StringUtils.hasText(deviceDesc)) {
            device.setDeviceDescription(deviceDesc);
        }
        device.setDeviceStatus("ENABLE");
        device.setConnectStatus("OFFLINE");
        // 注意：Device VO 中没有 protocolType 字段，协议类型信息应该在产品中

        // 调用远程服务注册设备
        // 注意：RemoteDeviceService中没有直接的注册方法，需要通过HTTP调用设备注册接口
        try {
            String rpcUrl = gatewayProperties.getRpc().getUrl();
            String registerUrl = rpcUrl + "/device";
            R<Device> registerResult = restTemplate.postForObject(registerUrl, device, R.class);
            if (registerResult != null && registerResult.getCode() == R.SUCCESS && registerResult.getData() != null) {
                log.info("[registerDevice][设备注册成功，productKey: {}, uniqueNo: {}]", productKey, uniqueNo);
                return registerResult.getData();
            } else {
                log.error("[registerDevice][设备注册失败，productKey: {}, uniqueNo: {}]", productKey, uniqueNo);
                throw new RuntimeException("设备注册失败");
            }
        } catch (Exception e) {
            log.error("[registerDevice][设备注册异常，productKey: {}, uniqueNo: {}]", productKey, uniqueNo, e);
            throw new RuntimeException("设备注册异常: " + e.getMessage(), e);
        }
    }

    /**
     * 构建注册响应
     *
     * @param productIdentification    产品标识
     * @param deviceIdentification    设备标识
     * @param deviceSecret  设备密钥
     * @return 注册响应
     */
    @Override
    public RegisterResp buildRegisterResp(String productIdentification, String deviceIdentification, String deviceSecret) {
        RegisterResp resp = new RegisterResp();
        resp.setProductIdentification(productIdentification);
        resp.setDeviceIdentification(deviceIdentification);
        resp.setDeviceSecret(deviceSecret);

        // 获取MQTT连接信息
        IotGatewayProperties.MqttProperties mqttProperties = gatewayProperties.getProtocol().getMqtt();
        if (mqttProperties != null && mqttProperties.getEnabled()) {
            // 使用MQTT协议配置
            resp.setMqttPort(mqttProperties.getPort());
            // 这里需要获取实际的MQTT服务器IP，可以从配置中获取或使用默认值
            resp.setMqttIp("127.0.0.1"); // 默认值，实际应该从配置中获取
        } else {
            // 使用EMQX配置
            IotGatewayProperties.EmqxProperties emqxProperties = gatewayProperties.getProtocol().getEmqx();
            if (emqxProperties != null && emqxProperties.getEnabled()) {
                resp.setMqttIp(emqxProperties.getMqttHost());
                resp.setMqttPort(emqxProperties.getMqttPort());
            }
        }

        return resp;
    }
}

