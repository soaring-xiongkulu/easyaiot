package com.basiclab.iot.sink.util;

import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.digest.DigestUtil;
import lombok.extern.slf4j.Slf4j;

import java.util.UUID;

/**
 * AppKeyUtils
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class AppKeyUtils {

    /**
     * 字符集：a-z, 0-9, A-Z，共62个字符
     */
    private static final String[] CHARS = new String[]{
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
            "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    };

    /**
     * 生成AppId
     * <p>
     * 算法：将UUID去掉横线，分成8组，每组4个字符，将每组16进制字符串转为10进制int，
     * 然后模62，从字符集中取对应字符，共8个字符
     *
     * @return AppId（8位字符串）
     */
    public static String generateAppId() {
        String uuid = UUID.randomUUID().toString().replace("-", "");
        StringBuilder appId = new StringBuilder();

        for (int i = 0; i < 8; i++) {
            String str = uuid.substring(i * 4, i * 4 + 4);
            int x = Integer.parseInt(str, 16);
            appId.append(CHARS[x % 0x3E]); // 0x3E = 62
        }

        return appId.toString();
    }

    /**
     * 生成AppKey
     * <p>
     * 算法：与AppId相同
     *
     * @return AppKey（8位字符串）
     */
    public static String generateAppKey() {
        return generateAppId();
    }

    /**
     * 生成AppSecret
     * <p>
     * 算法：使用SHA1对 appId + UUID 进行哈希，生成32位十六进制字符串
     *
     * @param appId 应用ID
     * @return AppSecret（32位十六进制字符串）
     */
    public static String generateAppSecret(String appId) {
        if (StrUtil.isBlank(appId)) {
            throw new IllegalArgumentException("AppId不能为空");
        }
        String uuid = UUID.randomUUID().toString().replace("-", "");
        String content = appId + uuid;
        return DigestUtil.sha1Hex(content);
    }

    /**
     * 生成AppId、AppKey、AppSecret
     *
     * @return AppKeyPair对象，包含appId、appKey、appSecret
     */
    public static AppKeyPair generateAppKeyPair() {
        String appId = generateAppId();
        String appKey = generateAppKey();
        String appSecret = generateAppSecret(appId);
        return new AppKeyPair(appId, appKey, appSecret);
    }

    /**
     * App密钥对
     */
    public static class AppKeyPair {
        private final String appId;
        private final String appKey;
        private final String appSecret;

        public AppKeyPair(String appId, String appKey, String appSecret) {
            this.appId = appId;
            this.appKey = appKey;
            this.appSecret = appSecret;
        }

        public String getAppId() {
            return appId;
        }

        public String getAppKey() {
            return appKey;
        }

        public String getAppSecret() {
            return appSecret;
        }

        @Override
        public String toString() {
            return "AppKeyPair{" +
                    "appId='" + appId + '\'' +
                    ", appKey='" + appKey + '\'' +
                    ", appSecret='" + appSecret + '\'' +
                    '}';
        }
    }
}

