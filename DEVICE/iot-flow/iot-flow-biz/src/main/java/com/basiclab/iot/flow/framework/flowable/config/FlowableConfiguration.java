package com.basiclab.iot.flow.framework.flowable.config;

import com.basiclab.iot.flow.framework.flowable.listener.FlowGlobalEventListener;
import org.flowable.spring.SpringProcessEngineConfiguration;
import org.flowable.spring.boot.EngineConfigurationConfigurer;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

/**
 * Flowable 引擎配置：
 *  - 注册全局事件监听（任务创建指派候选人 / 实例结束回写告警记录）；
 *  - 关闭异步执行器（审批链路全部同步，行为可预期）。
 *
 * 监听器在事件触发时才从 ApplicationContext 取业务 Bean，
 * 避免引擎构建期与 RepositoryService 等引擎服务 Bean 的循环依赖。
 */
@Configuration
public class FlowableConfiguration {

    @Bean
    public EngineConfigurationConfigurer<SpringProcessEngineConfiguration> flowEngineConfigurer(
            ApplicationContext applicationContext) {
        return configuration -> configuration.setEventListeners(
                List.of(new FlowGlobalEventListener(applicationContext)));
    }

}
