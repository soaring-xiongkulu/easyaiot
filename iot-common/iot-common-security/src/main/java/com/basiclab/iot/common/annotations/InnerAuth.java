package com.basiclab.iot.common.annotations;

import java.lang.annotation.*;

/**
 * 内部认证注解
 * 
 * @author 深圳市深度智核科技有限责任公司
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface InnerAuth
{
    /**
     * 是否校验用户信息
     */
    boolean isUser() default false;
}