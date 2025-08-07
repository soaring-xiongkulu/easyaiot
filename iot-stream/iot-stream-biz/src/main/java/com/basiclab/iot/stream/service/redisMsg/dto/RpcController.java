package com.basiclab.iot.stream.service.redisMsg.dto;


import com.basiclab.iot.stream.config.redis.RedisRpcConfig;
import com.basiclab.iot.stream.config.redis.bean.RedisRpcClassHandler;
import org.springframework.beans.factory.annotation.Autowired;

import javax.annotation.PostConstruct;
import java.lang.reflect.Method;

public class RpcController {

    @Autowired
    private RedisRpcConfig redisRpcConfig;


    @PostConstruct
    public void init() {
        String controllerPath = this.getClass().getAnnotation(RedisRpcController.class).value();
        // 扫描其下的方法
        Method[] methods = this.getClass().getDeclaredMethods();
        for (Method method : methods) {
            RedisRpcMapping annotation = method.getAnnotation(RedisRpcMapping.class);
            if (annotation != null) {
                String methodPath =  annotation.value();
                if (methodPath != null) {
                    redisRpcConfig.addHandler(controllerPath + "/" + methodPath, new RedisRpcClassHandler(this, method));
                }
            }

        }
    }
}
