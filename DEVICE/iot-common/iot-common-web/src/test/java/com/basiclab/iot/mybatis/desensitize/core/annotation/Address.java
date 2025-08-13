package com.basiclab.iot.mybatis.desensitize.core.annotation;

import com.basiclab.iot.common.desensitize.core.base.annotation.DesensitizeBy;
import com.basiclab.iot.mybatis.desensitize.core.DesensitizeTest;
import com.basiclab.iot.mybatis.desensitize.core.handler.AddressHandler;
import com.fasterxml.jackson.annotation.JacksonAnnotationsInside;

import java.lang.annotation.*;

/**
 * 地址
 * <p>
 * 用于 {@link DesensitizeTest} 测试使用
 *
 * @author gaibu
 */
@Documented
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@JacksonAnnotationsInside
@DesensitizeBy(handler = AddressHandler.class)
public @interface Address {

    String replacer() default "*";

}
