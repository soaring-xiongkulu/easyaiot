package com.basiclab.iot.common.utils;

import cn.hutool.crypto.digest.DigestUtil;
import cn.hutool.crypto.digest.HmacAlgorithm;
import lombok.extern.slf4j.Slf4j;

/**
 * 签名工具类
 * <p>
 * 支持 hmacmd5、hmacsha1、hmacsha256 签名和验签
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
public class SignUtils {

    /**
     * 签名方法枚举
     */
    public enum SignMethod {
        HMAC_MD5("hmacmd5", HmacAlgorithm.HmacMD5),
        HMAC_SHA1("hmacsha1", HmacAlgorithm.HmacSHA1),
        HMAC_SHA256("hmacsha256", HmacAlgorithm.HmacSHA256);

        private final String method;
        private final HmacAlgorithm algorithm;

        SignMethod(String method, HmacAlgorithm algorithm) {
            this.method = method;
            this.algorithm = algorithm;
        }

        public String getMethod() {
            return method;
        }

        public HmacAlgorithm getAlgorithm() {
            return algorithm;
        }

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
    }

    /**
     * 计算签名
     *
     * @param content     待签名的内容
     * @param secret      密钥
     * @param signMethod  签名方法
     * @return 签名结果（十六进制字符串）
     */
    public static String sign(String content, String secret, SignMethod signMethod) {
        if (signMethod == null) {
            throw new IllegalArgumentException("签名方法不能为空");
        }
        if (content == null) {
            throw new IllegalArgumentException("待签名内容不能为空");
        }
        if (secret == null) {
            throw new IllegalArgumentException("密钥不能为空");
        }

        try {
            return DigestUtil.hmac(signMethod.getAlgorithm(), secret.getBytes())
                    .digestHex(content);
        } catch (Exception e) {
            log.error("[sign][签名计算失败，signMethod: {}, content: {}]", signMethod.getMethod(), content, e);
            throw new RuntimeException("签名计算失败: " + e.getMessage(), e);
        }
    }

    /**
     * 验证签名
     *
     * @param content     待签名的内容
     * @param secret      密钥
     * @param sign        待验证的签名
     * @param signMethod  签名方法
     * @return 验证结果，true表示验证通过
     */
    public static boolean verify(String content, String secret, String sign, SignMethod signMethod) {
        if (signMethod == null) {
            log.warn("[verify][签名方法为空]");
            return false;
        }
        if (content == null || secret == null || sign == null) {
            log.warn("[verify][参数不完整，content: {}, secret: {}, sign: {}]", content, secret, sign);
            return false;
        }

        try {
            String calculatedSign = sign(content, secret, signMethod);
            boolean result = calculatedSign.equalsIgnoreCase(sign);
            if (!result) {
                log.warn("[verify][签名验证失败，signMethod: {}, calculatedSign: {}, providedSign: {}]",
                        signMethod.getMethod(), calculatedSign, sign);
            }
            return result;
        } catch (Exception e) {
            log.error("[verify][签名验证异常，signMethod: {}, content: {}]", signMethod.getMethod(), content, e);
            return false;
        }
    }

    /**
     * 根据方法名称计算签名
     *
     * @param content    待签名的内容
     * @param secret     密钥
     * @param methodName 签名方法名称（hmacmd5、hmacsha1、hmacsha256）
     * @return 签名结果（十六进制字符串）
     */
    public static String sign(String content, String secret, String methodName) {
        SignMethod signMethod = SignMethod.get(methodName);
        if (signMethod == null) {
            throw new IllegalArgumentException("不支持的签名方法: " + methodName);
        }
        return sign(content, secret, signMethod);
    }

    /**
     * 根据方法名称验证签名
     *
     * @param content    待签名的内容
     * @param secret     密钥
     * @param sign       待验证的签名
     * @param methodName 签名方法名称（hmacmd5、hmacsha1、hmacsha256）
     * @return 验证结果，true表示验证通过
     */
    public static boolean verify(String content, String secret, String sign, String methodName) {
        SignMethod signMethod = SignMethod.get(methodName);
        if (signMethod == null) {
            log.warn("[verify][不支持的签名方法: {}]", methodName);
            return false;
        }
        return verify(content, secret, sign, signMethod);
    }
}

