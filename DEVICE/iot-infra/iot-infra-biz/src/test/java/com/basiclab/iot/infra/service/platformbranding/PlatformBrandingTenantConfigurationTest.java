package com.basiclab.iot.infra.service.platformbranding;

import cn.hutool.core.io.IoUtil;
import org.junit.jupiter.api.Test;

import java.io.InputStream;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 平台品牌配置的全局租户隔离规则测试。
 */
public class PlatformBrandingTenantConfigurationTest {

    @Test
    public void testPlatformBranding_isGlobalTenantConfiguration() {
        InputStream inputStream = getClass().getClassLoader().getResourceAsStream("application.yaml");
        assertNotNull(inputStream);
        String applicationConfig = IoUtil.readUtf8(inputStream);

        assertTrue(applicationConfig.contains("- /admin-api/infra/platform-branding/get"));
        assertTrue(applicationConfig.contains("- /admin-api/infra/platform-branding/image/view"));
        assertTrue(applicationConfig.contains("- infra_platform_branding"));
    }
}
