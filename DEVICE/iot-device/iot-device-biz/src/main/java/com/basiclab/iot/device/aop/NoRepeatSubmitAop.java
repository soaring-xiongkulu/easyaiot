package com.basiclab.iot.device.aop;

import com.basiclab.iot.common.annotation.NoRepeatSubmit;
import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.common.utils.SecurityUtils;
import com.basiclab.iot.common.domain.AjaxResult;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;
import java.util.concurrent.TimeUnit;


/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @功能描述 防止多次提交aop解析注解
 * @date 2022-02-15
 */
@Slf4j
@Aspect
@Component
public class NoRepeatSubmitAop {

    @Autowired
    private RedisService redisService;

    @Around("execution(* com.basiclab.iot.device.controller..*.*(..)) && @annotation(nrs)")
    public Object arround(ProceedingJoinPoint pjp, NoRepeatSubmit nrs) {
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            HttpServletRequest request = attributes.getRequest();
            log.info("请求地址：{}", request.getServletPath());
            String key = SecurityUtils.getToken() + "-" + request.getServletPath();
            log.info("newToken:{}", key);
            if (!redisService.hasKey(Constants.RESUBMIT_URL_KEY+key)) {// 如果缓存中有这个url视为重复提交
                redisService.setCacheObject(Constants.RESUBMIT_URL_KEY+key, pjp.toString(), 10L, TimeUnit.SECONDS);
                return pjp.proceed();
            } else {
                log.error("请勿频繁操作，请稍后再试！");
                return AjaxResult.error("请勿频繁操作，请稍后再试！");
            }
        } catch (Throwable e) {
            e.printStackTrace();
            log.error("验证重复提交时出现未知异常!");
            return AjaxResult.error("内部服务异常!");
        }
    }

}