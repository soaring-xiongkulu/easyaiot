package com.basiclab.iot.stream.config.redis.bean;

import com.basiclab.iot.stream.service.redisMsg.dto.RpcController;
import lombok.Data;

import java.lang.reflect.Method;

@Data
public class RedisRpcClassHandler {

    private RpcController controller;
    private Method method;

    public RedisRpcClassHandler(RpcController controller, Method method) {
        this.controller = controller;
        this.method = method;
    }
}
