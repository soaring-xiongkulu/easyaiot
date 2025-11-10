package com.basiclab.iot.common.ratelimiter.core.keyresolver.impl;

import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.SecureUtil;
import com.basiclab.iot.common.ratelimiter.core.annotation.RateLimiter;
import com.basiclab.iot.common.ratelimiter.core.keyresolver.RateLimiterKeyResolver;
import com.basiclab.iot.common.web.core.util.WebFrameworkUtils;
import org.aspectj.lang.JoinPoint;

/**
 * 用户级别的限流 Key 解析器，使用方法名 + 方法参数 + userId + userType，组装成一个 Key
 * <p>
 * 为了避免 Key 过长，使用 MD5 进行“压缩”
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class UserRateLimiterKeyResolver implements RateLimiterKeyResolver {

    @Override
    public String resolver(JoinPoint joinPoint, RateLimiter rateLimiter) {
        String methodName = joinPoint.getSignature().toString();
        String argsStr = StrUtil.join(",", joinPoint.getArgs());
        Long userId = WebFrameworkUtils.getLoginUserId();
        Integer userType = WebFrameworkUtils.getLoginUserType();
        return SecureUtil.md5(methodName + argsStr + userId + userType);
    }

}
