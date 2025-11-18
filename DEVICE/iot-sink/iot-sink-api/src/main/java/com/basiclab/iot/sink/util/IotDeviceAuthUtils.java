package com.basiclab.iot.sink.util;

import cn.hutool.crypto.digest.DigestUtil;
import cn.hutool.crypto.digest.HmacAlgorithm;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * IotDeviceAuthUtils
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class IotDeviceAuthUtils {

    /**
     * 认证信息
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AuthInfo {

        /**
         * 客户端 ID
         */
        private String clientId;

        /**
         * 用户名
         */
        private String username;

        /**
         * 密码
         */
        private String password;

    }

    /**
     * 设备信息
     */
    @Data
    public static class DeviceInfo {

        private String productIdentification;

        private String deviceIdentification;

    }

    public static AuthInfo getAuthInfo(String productIdentification, String deviceIdentification, String deviceSecret) {
        String clientId = buildClientId(productIdentification, deviceIdentification);
        String username = buildUsername(productIdentification, deviceIdentification);
        String content = "clientId" + clientId +
                "deviceIdentification" + deviceIdentification +
                "deviceSecret" + deviceSecret +
                "productIdentification" + productIdentification;
        String password = buildPassword(deviceSecret, content);
        return new AuthInfo(clientId, username, password);
    }

    private static String buildClientId(String productIdentification, String deviceIdentification) {
        return String.format("%s.%s", productIdentification, deviceIdentification);
    }

    private static String buildUsername(String productIdentification, String deviceIdentification) {
        return String.format("%s&%s", deviceIdentification, productIdentification);
    }

    private static String buildPassword(String deviceSecret, String content) {
        return DigestUtil.hmac(HmacAlgorithm.HmacSHA256, deviceSecret.getBytes())
                .digestHex(content);
    }

    public static DeviceInfo parseUsername(String username) {
        String[] usernameParts = username.split("&");
        if (usernameParts.length != 2) {
            return null;
        }
        return new DeviceInfo().setProductIdentification(usernameParts[1]).setDeviceIdentification(usernameParts[0]);
    }

}
