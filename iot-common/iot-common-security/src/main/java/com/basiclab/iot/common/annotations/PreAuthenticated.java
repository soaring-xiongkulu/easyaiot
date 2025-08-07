package com.basiclab.iot.common.annotations;

import java.lang.annotation.*;

/**
 * 声明用户需要登录
 *
 * 为什么不使用 {@link org.springframework.security.access.prepost.PreAuthorize} 注解，原因是不通过时，抛出的是认证不通过，而不是未登录
 *
 * @author 深圳市深度智核科技有限责任公司源码
 */
@Target({ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Documented
public @interface PreAuthenticated {
}
