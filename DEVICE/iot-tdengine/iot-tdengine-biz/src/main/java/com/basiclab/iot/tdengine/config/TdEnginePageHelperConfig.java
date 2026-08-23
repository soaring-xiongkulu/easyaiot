package com.basiclab.iot.tdengine.config;

import com.github.pagehelper.PageInterceptor;
import lombok.extern.slf4j.Slf4j;
import org.apache.ibatis.plugin.Interceptor;
import org.apache.ibatis.session.SqlSessionFactory;
import org.springframework.context.ApplicationListener;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.stereotype.Component;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.List;
import java.util.Properties;

/**
 * 兜底：PageHelper 拦截器被 MyBatis Plugin 代理包装，需在启动后解包并补全方言配置。
 */
@Slf4j
@Component
public class TdEnginePageHelperConfig implements ApplicationListener<ContextRefreshedEvent> {

    private final List<SqlSessionFactory> sqlSessionFactoryList;

    public TdEnginePageHelperConfig(List<SqlSessionFactory> sqlSessionFactoryList) {
        this.sqlSessionFactoryList = sqlSessionFactoryList;
    }

    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        if (event.getApplicationContext().getParent() != null) {
            return;
        }
        Properties properties = buildPageHelperProperties();

        int configured = 0;
        for (SqlSessionFactory sqlSessionFactory : sqlSessionFactoryList) {
            for (Interceptor interceptor : sqlSessionFactory.getConfiguration().getInterceptors()) {
                PageInterceptor pageInterceptor = resolvePageInterceptor(interceptor);
                if (pageInterceptor != null) {
                    pageInterceptor.setProperties(properties);
                    configured++;
                }
            }
        }
        if (configured > 0) {
            log.info("TDengine PageHelper configured on {} interceptor(s): helperDialect=mysql, autoDialect=false", configured);
        } else {
            log.warn("TDengine PageHelper: no PageInterceptor found on SqlSessionFactory, pagination may fail");
        }
    }

    static Properties buildPageHelperProperties() {
        Properties properties = new Properties();
        properties.setProperty("helperDialect", "mysql");
        properties.setProperty("autoDialect", "false");
        properties.setProperty("reasonable", "true");
        properties.setProperty("supportMethodsArguments", "true");
        return properties;
    }

    static PageInterceptor resolvePageInterceptor(Interceptor interceptor) {
        Interceptor current = interceptor;
        for (int depth = 0; depth < 5 && current != null; depth++) {
            if (current instanceof PageInterceptor) {
                return (PageInterceptor) current;
            }
            current = unwrapInterceptor(current);
        }
        return null;
    }

    private static Interceptor unwrapInterceptor(Interceptor interceptor) {
        if (interceptor == null) {
            return null;
        }
        if (Proxy.isProxyClass(interceptor.getClass())) {
            try {
                InvocationHandler handler = Proxy.getInvocationHandler(interceptor);
                Object target = readField(handler, "target");
                if (target instanceof Interceptor) {
                    return (Interceptor) target;
                }
            } catch (Exception ignored) {
                // fall through
            }
        }
        if ("org.apache.ibatis.plugin.Plugin".equals(interceptor.getClass().getName())) {
            Object target = readField(interceptor, "target");
            if (target instanceof Interceptor) {
                return (Interceptor) target;
            }
        }
        return null;
    }

    private static Object readField(Object target, String fieldName) {
        Class<?> type = target.getClass();
        while (type != null) {
            try {
                Field field = type.getDeclaredField(fieldName);
                field.setAccessible(true);
                return field.get(target);
            } catch (Exception ignored) {
                type = type.getSuperclass();
            }
        }
        return null;
    }
}
