package com.basiclab.iot.common.ratelimiter.core.aop;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.common.exception.GlobalErrorStatus;
import com.basiclab.iot.common.utils.collection.CollectionUtils;
import com.basiclab.iot.common.ratelimiter.core.annotation.RateLimiter;
import com.basiclab.iot.common.ratelimiter.core.keyresolver.RateLimiterKeyResolver;
import com.basiclab.iot.common.ratelimiter.core.redis.RateLimiterRedisDAO;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.springframework.util.Assert;

import java.util.List;
import java.util.Map;

/**
 * 拦截声明了 {@link RateLimiter} 注解的方法，实现限流操作
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Aspect
@Slf4j
public class RateLimiterAspect {

    /**
     * RateLimiterKeyResolver 集合
     */
    private final Map<Class<? extends RateLimiterKeyResolver>, RateLimiterKeyResolver> keyResolvers;

    private final RateLimiterRedisDAO rateLimiterRedisMapper;

    public RateLimiterAspect(List<RateLimiterKeyResolver> keyResolvers, RateLimiterRedisDAO rateLimiterRedisMapper) {
        this.keyResolvers = CollectionUtils.convertMap(keyResolvers, RateLimiterKeyResolver::getClass);
        this.rateLimiterRedisMapper = rateLimiterRedisMapper;
    }

    @Before("@annotation(rateLimiter)")
    public void beforePointCut(JoinPoint joinPoint, RateLimiter rateLimiter) {
        // 获得 IdempotentKeyResolver 对象
        RateLimiterKeyResolver keyResolver = keyResolvers.get(rateLimiter.keyResolver());
        Assert.notNull(keyResolver, "找不到对应的 RateLimiterKeyResolver");
        // 解析 Key
        String key = keyResolver.resolver(joinPoint, rateLimiter);

        // 获取 1 次限流
        boolean success = rateLimiterRedisMapper.tryAcquire(key,
                rateLimiter.count(), rateLimiter.time(), rateLimiter.timeUnit());
        if (!success) {
            log.info("[beforePointCut][方法({}) 参数({}) 请求过于频繁]", joinPoint.getSignature().toString(), joinPoint.getArgs());
            String message = StrUtil.blankToDefault(rateLimiter.message(),
                    GlobalErrorStatus.TOO_MANY_REQUESTS.getMsg());
            throw new ServiceException(GlobalErrorStatus.TOO_MANY_REQUESTS.getCode(), message);
        }
    }

}

