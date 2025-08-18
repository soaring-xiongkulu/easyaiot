package com.basiclab.iot.gateway.filter.demo;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.cloud.gateway.filter.NettyWriteResponseFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;

/**
 * 演示环境拦截过滤器 - 阻止写操作保护测试数据
 * 执行顺序：Netty响应写入后（确保优先级高于响应修改过滤器）
 */
@Component
public class DemoBlockFilter implements GlobalFilter, Ordered {

    // 演示环境拒绝提示
    private static final String DEMO_DENY_MSG = "{\"code\": \"DEMO_DENY\", \"msg\": \"演示环境禁止写操作\"}";

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        // 1. 跳过非写请求和未登录用户
        if (!isWriteMethod(request.getMethod()) || !isUserLoggedIn(request)) {
            return chain.filter(exchange);
        }

        // 2. 拦截写操作并返回错误
        return writeDenyResponse(exchange.getResponse());
    }

    /**
     * 判断是否为写操作
     */
    private boolean isWriteMethod(HttpMethod method) {
        return method == HttpMethod.POST
                || method == HttpMethod.PUT
                || method == HttpMethod.DELETE;
    }

    /**
     * 判断用户是否登录（根据实际鉴权逻辑调整）
     * 示例：检查Authorization头是否存在
     */
    private boolean isUserLoggedIn(ServerHttpRequest request) {
        return request.getHeaders().containsKey("Authorization");
    }

    /**
     * 写入拒绝响应
     */
    private Mono<Void> writeDenyResponse(ServerHttpResponse response) {
        response.setStatusCode(HttpStatus.OK);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        DataBuffer buffer = response.bufferFactory()
                .wrap(DEMO_DENY_MSG.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    /**
     * 设置执行顺序（在响应写入后执行）
     */
    @Override
    public int getOrder() {
        return NettyWriteResponseFilter.WRITE_RESPONSE_FILTER_ORDER + 10;
    }
}