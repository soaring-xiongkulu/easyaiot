package com.basiclab.iot.common.aop;

import com.basiclab.iot.common.annotations.PreAuthenticated;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;

import static com.basiclab.iot.common.exception.GlobalErrorStatus.UNAUTHORIZED;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

@Aspect
@Slf4j
public class PreAuthenticatedAspect {

    @Around("@annotation(preAuthenticated)")
    public Object around(ProceedingJoinPoint joinPoint, PreAuthenticated preAuthenticated) throws Throwable {
        if (SecurityFrameworkUtils.getLoginUser() == null) {
            throw exception(UNAUTHORIZED);
        }
        return joinPoint.proceed();
    }

}
