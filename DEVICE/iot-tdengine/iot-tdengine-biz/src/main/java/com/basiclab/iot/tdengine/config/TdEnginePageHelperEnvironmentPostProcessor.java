package com.basiclab.iot.tdengine.config;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.MapPropertySource;

import java.util.HashMap;
import java.util.Map;

/**
 * 在 PageHelper 自动配置之前注入方言，避免 TDengine JDBC 无法被 autoDialect 识别。
 */
public class TdEnginePageHelperEnvironmentPostProcessor implements EnvironmentPostProcessor {

    private static final String PROPERTY_SOURCE = "tdenginePageHelper";

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        Map<String, Object> properties = new HashMap<>(4);
        properties.put("pagehelper.helper-dialect", "mysql");
        properties.put("pagehelper.auto-dialect", "false");
        properties.put("pagehelper.reasonable", "true");
        properties.put("pagehelper.support-methods-arguments", "true");
        environment.getPropertySources().addFirst(new MapPropertySource(PROPERTY_SOURCE, properties));
    }
}
