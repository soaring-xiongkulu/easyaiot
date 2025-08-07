package com.basiclab.iot.stream.enums;

import com.basiclab.iot.common.enums.RpcConstants;

/**
 * API 相关的枚举
 *
 * @author 安徽上洲智能科技
 */
public class ApiConstants {

    /**
     * 服务名
     *
     * 注意，需要保证和 spring.application.name 保持一致
     */
    public static final String NAME = "stream-server";

    public static final String PREFIX = RpcConstants.RPC_API_PREFIX + "/stream";

    public static final String VERSION = "1.0.0";

}
