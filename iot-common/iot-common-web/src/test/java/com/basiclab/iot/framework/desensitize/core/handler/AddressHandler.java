package com.basiclab.iot.common.desensitize.core.handler;

import com.basiclab.iot.common.desensitize.core.DesensitizeTest;
import com.basiclab.iot.common.desensitize.core.base.handler.DesensitizationHandler;
import com.basiclab.iot.common.desensitize.core.annotation.Address;

/**
 * {@link Address} 的脱敏处理器
 *
 * 用于 {@link DesensitizeTest} 测试使用
 */
public class AddressHandler implements DesensitizationHandler<Address> {

    @Override
    public String desensitize(String origin, Address annotation) {
        return origin + annotation.replacer();
    }

}
