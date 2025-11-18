package com.basiclab.iot.sink.messagebus.subscriber.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * IotMessageBusSubscriberThreadPoolConfig
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Configuration
@EnableAsync
public class IotMessageBusSubscriberThreadPoolConfig {

    /**
     * 核心线程数
     */
    private static final int CORE_POOL_SIZE = 20;

    /**
     * 最大线程数
     */
    private static final int MAX_POOL_SIZE = 100;

    /**
     * 队列容量
     */
    private static final int QUEUE_CAPACITY = 500;

    /**
     * 线程名前缀
     */
    private static final String THREAD_NAME_PREFIX = "iot-messagebus-subscriber-";

    /**
     * 线程空闲时间（秒）
     */
    private static final int KEEP_ALIVE_SECONDS = 60;

    @Bean(name = "iotMessageBusSubscriberExecutor")
    public Executor iotMessageBusSubscriberExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(CORE_POOL_SIZE);
        executor.setMaxPoolSize(MAX_POOL_SIZE);
        executor.setQueueCapacity(QUEUE_CAPACITY);
        executor.setThreadNamePrefix(THREAD_NAME_PREFIX);
        executor.setKeepAliveSeconds(KEEP_ALIVE_SECONDS);
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        log.info("[iotMessageBusSubscriberExecutor][IoT 消息总线订阅处理线程池初始化完成，核心线程数: {}, 最大线程数: {}, 队列容量: {}]",
                CORE_POOL_SIZE, MAX_POOL_SIZE, QUEUE_CAPACITY);
        return executor;
    }
}

