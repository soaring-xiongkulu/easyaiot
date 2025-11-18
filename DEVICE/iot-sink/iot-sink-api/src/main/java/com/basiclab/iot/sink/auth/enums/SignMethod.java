package com.basiclab.iot.sink.auth.enums;

import cn.hutool.crypto.digest.DigestUtil;
import cn.hutool.crypto.digest.HmacAlgorithm;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * SignMethod
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Getter
@AllArgsConstructor
public enum SignMethod {

    HMAC_MD5("hmacmd5", HmacAlgorithm.HmacMD5),
    HMAC_SHA1("hmacsha1", HmacAlgorithm.HmacSHA1),
    HMAC_SHA256("hmacsha256", HmacAlgorithm.HmacSHA256);

    /**
     * 签名方法名称
     */
    private final String method;

    /**
     * HMAC算法
     */
    private final HmacAlgorithm algorithm;

    /**
     * 根据方法名称获取签名方法
     *
     * @param method 方法名称
     * @return 签名方法，如果不存在则返回null
     */
    public static SignMethod get(String method) {
        if (method == null) {
            return null;
        }
        for (SignMethod signMethod : values()) {
            if (signMethod.getMethod().equalsIgnoreCase(method)) {
                return signMethod;
            }
        }
        return null;
    }

    /**
     * 计算签名
     *
     * @param content 待签名的内容
     * @param secret  密钥
     * @return 签名结果（十六进制字符串）
     */
    public String sign(String content, String secret) {
        return DigestUtil.hmac(this.algorithm, secret.getBytes())
                .digestHex(content);
    }
}

