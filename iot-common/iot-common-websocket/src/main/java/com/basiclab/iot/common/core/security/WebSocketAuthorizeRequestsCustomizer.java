package com.basiclab.iot.common.core.security;

import com.basiclab.iot.common.config.AuthorizeRequestsCustomizer;
import com.basiclab.iot.common.config.WebSocketProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.ExpressionUrlAuthorizationConfigurer;

/**
 * WebSocket 的权限自定义
 *
 * @author 深圳市深度智核科技有限责任公司
 */
@RequiredArgsConstructor
public class WebSocketAuthorizeRequestsCustomizer extends AuthorizeRequestsCustomizer {

    private final WebSocketProperties webSocketProperties;

    @Override
    public void customize(ExpressionUrlAuthorizationConfigurer<HttpSecurity>.ExpressionInterceptUrlRegistry registry) {
        registry.antMatchers(webSocketProperties.getPath()).permitAll();
    }

}
