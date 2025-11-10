package com.basiclab.iot.common.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 权限注解
 * 
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Target({ ElementType.TYPE, ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
public @interface PreAuthorize
{
    /**
     * 验证用户是否具备某权限
     */
    public String hasPermi() default "";

    /**
     * 验证用户是否不具备某权限，与 hasPermi逻辑相反
     */
    public String lacksPermi() default "";

    /**
     * 验证用户是否具有以下任意一个权限
     */
    public String[] hasAnyPermi() default {};

    /**
     * 判断用户是否拥有某个角色
     */
    public String hasRole() default "";

    /**
     * 验证用户是否不具备某角色，与 isRole逻辑相反
     */
    public String lacksRole() default "";

    /**
     * 验证用户是否具有以下任意一个角色
     */
    public String[] hasAnyRoles() default {};
}