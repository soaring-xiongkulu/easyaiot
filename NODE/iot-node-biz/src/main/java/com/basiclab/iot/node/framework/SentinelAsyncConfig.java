package com.basiclab.iot.node.framework;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

@Configuration
public class SentinelAsyncConfig {

    @Bean(name = "sentinelBootstrapExecutor")
    public Executor sentinelBootstrapExecutor() {
        ThreadPoolExecutor executor = new ThreadPoolExecutor(
                1,
                4,
                60,
                TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(32),
                r -> {
                    Thread t = new Thread(r, "sentinel-bootstrap");
                    t.setDaemon(true);
                    return t;
                },
                new ThreadPoolExecutor.CallerRunsPolicy());
        executor.allowCoreThreadTimeOut(true);
        return executor;
    }
}
