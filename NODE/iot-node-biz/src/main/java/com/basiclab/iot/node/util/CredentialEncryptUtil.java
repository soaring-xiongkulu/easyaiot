package com.basiclab.iot.node.util;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.SecureUtil;
import cn.hutool.crypto.symmetric.AES;
import cn.hutool.extra.spring.SpringUtil;

import java.nio.charset.StandardCharsets;

/**
 * SSH 凭据加解密工具，密钥复用 mybatis-plus.encryptor.password 配置
 */
public final class CredentialEncryptUtil {

    private static final String ENCRYPTOR_PROPERTY_NAME = "mybatis-plus.encryptor.password";

    private static AES aes;

    private CredentialEncryptUtil() {
    }

    public static String encrypt(String plainText) {
        if (StrUtil.isBlank(plainText)) {
            return plainText;
        }
        return getEncryptor().encryptBase64(plainText);
    }

    public static String decrypt(String cipherText) {
        if (StrUtil.isBlank(cipherText)) {
            return cipherText;
        }
        return getEncryptor().decryptStr(cipherText);
    }

    private static AES getEncryptor() {
        if (aes != null) {
            return aes;
        }
        String password = SpringUtil.getProperty(ENCRYPTOR_PROPERTY_NAME);
        Assert.notEmpty(password, "配置项({}) 不能为空", ENCRYPTOR_PROPERTY_NAME);
        aes = SecureUtil.aes(password.getBytes(StandardCharsets.UTF_8));
        return aes;
    }

}
