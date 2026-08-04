package com.basiclab.iot.infra.service.platformbranding;

import com.basiclab.iot.infra.dal.dataobject.file.FileDO;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

/**
 * 品牌图片公开地址测试。
 */
public class PlatformBrandingFileUrlBuilderTest {

    @Test
    public void testBuild_usesExtensionlessBrandingImageRoute() {
        FileDO file = new FileDO();
        file.setId(7L);
        file.setPath("branding/platform-logo.png");

        String url = PlatformBrandingFileUrlBuilder.build(file);

        assertEquals("/admin-api/infra/platform-branding/image/view?fileId=7", url);
        assertFalse(url.endsWith(".png"));
    }
}
