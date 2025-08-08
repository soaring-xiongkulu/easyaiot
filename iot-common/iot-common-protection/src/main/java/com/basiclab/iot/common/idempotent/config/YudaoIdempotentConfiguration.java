package com.basiclab.iot.common.idempotent.config;

import com.basiclab.iot.common.idempotent.core.aop.IdempotentAspect;
import com.basiclab.iot.common.idempotent.core.keyresolver.IdempotentKeyResolver;
import com.basiclab.iot.common.idempotent.core.keyresolver.impl.DefaultIdempotentKeyResolver;
import com.basiclab.iot.common.idempotent.core.keyresolver.impl.ExpressionIdempotentKeyResolver;
import com.basiclab.iot.common.idempotent.core.redis.IdempotentRedisDAO;
import com.basiclab.iot.common.idempotent.core.keyresolver.impl.UserIdempotentKeyResolver;
import com.basiclab.iot.common.config.YudaoRedisAutoConfiguration;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.List;

@AutoConfiguration(after = YudaoRedisAutoConfiguration.class)
public class YudaoIdempotentConfiguration {

    @Bean
    public IdempotentAspect idempotentAspect(List<IdempotentKeyResolver> keyResolvers, IdempotentRedisDAO idempotentRedisMapper) {
        return new IdempotentAspect(keyResolvers, idempotentRedisMapper);
    }

    @Bean
    public IdempotentRedisDAO idempotentRedisMapper(StringRedisTemplate stringRedisTemplate) {
        return new IdempotentRedisDAO(stringRedisTemplate);
    }

    // ========== 各种 IdempotentKeyResolver Bean ==========

    @Bean
    public DefaultIdempotentKeyResolver defaultIdempotentKeyResolver() {
        return new DefaultIdempotentKeyResolver();
    }

    @Bean
    public UserIdempotentKeyResolver userIdempotentKeyResolver() {
        return new UserIdempotentKeyResolver();
    }

    @Bean
    public ExpressionIdempotentKeyResolver expressionIdempotentKeyResolver() {
        return new ExpressionIdempotentKeyResolver();
    }

}
