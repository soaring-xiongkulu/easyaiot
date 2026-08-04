package com.basiclab.iot.infra.service.platformbranding;

import com.basiclab.iot.common.core.ut.BaseDbUnitTest;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingRespVO;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingSaveReqVO;
import com.basiclab.iot.infra.dal.dataobject.file.FileDO;
import com.basiclab.iot.infra.dal.dataobject.platformbranding.PlatformBrandingDO;
import com.basiclab.iot.infra.dal.pgsql.file.FileMapper;
import com.basiclab.iot.infra.dal.pgsql.platformbranding.PlatformBrandingMapper;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Import;

import javax.annotation.Resource;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

/**
 * 平台品牌配置 Service 测试
 */
@Import(PlatformBrandingServiceImpl.class)
public class PlatformBrandingServiceImplTest extends BaseDbUnitTest {

    @Resource
    private PlatformBrandingServiceImpl platformBrandingService;

    @Resource
    private PlatformBrandingMapper platformBrandingMapper;

    @Resource
    private FileMapper fileMapper;

    @Test
    public void testGetPlatformBranding_noRecord() {
        PlatformBrandingRespVO response = platformBrandingService.getPlatformBranding();

        assertNotNull(response);
        assertNull(response.getPlatformName());
        assertNull(response.getPlatformLogo());
    }

    @Test
    public void testGetPlatformBranding_currentEmptyUsesDatabaseDefaults() {
        FileDO defaultLogo = createImageFile("https://files.example.com/default-logo.webp");
        PlatformBrandingDO config = new PlatformBrandingDO();
        config.setId(1L);
        config.setDefaultPlatformName("数据库初始平台");
        config.setDefaultPlatformLogoFileId(defaultLogo.getId());
        config.setDefaultDashboardTitle("数据库初始大屏");
        config.setDefaultLoginName("数据库初始登录页");
        config.setDefaultLoginFormTitle("数据库初始登录标题");
        platformBrandingMapper.insert(config);

        PlatformBrandingRespVO response = platformBrandingService.getPlatformBranding();

        assertEquals("数据库初始平台", response.getPlatformName());
        assertEquals(defaultLogo.getId(), response.getPlatformLogoFileId());
        assertEquals("/admin-api/infra/platform-branding/image/view?fileId=" + defaultLogo.getId(),
                response.getPlatformLogo());
        assertEquals("数据库初始大屏", response.getDashboardTitle());
        assertEquals("数据库初始登录页", response.getLoginName());
        assertEquals("数据库初始登录标题", response.getLoginFormTitle());
    }

    @Test
    public void testSavePlatformBranding_createAndResolveImageUrl() {
        FileDO logo = createImageFile("https://files.example.com/platform-logo.webp");
        PlatformBrandingSaveReqVO request = createSaveRequest();
        request.setPlatformLogoFileId(logo.getId());

        PlatformBrandingRespVO response = platformBrandingService.savePlatformBranding(request);

        assertEquals(1L, platformBrandingMapper.selectCount());
        assertEquals("测试平台", response.getPlatformName());
        assertEquals(logo.getId(), response.getPlatformLogoFileId());
        assertEquals("/admin-api/infra/platform-branding/image/view?fileId=" + logo.getId(),
                response.getPlatformLogo());
    }

    @Test
    public void testResetPlatformBranding_persistDefaults() {
        PlatformBrandingSaveReqVO request = createSaveRequest();
        request.setPlatformLogoFileId(createImageFile("https://files.example.com/custom.webp").getId());
        platformBrandingService.savePlatformBranding(request);

        PlatformBrandingRespVO response = platformBrandingService.resetPlatformBranding();

        PlatformBrandingDO stored = platformBrandingMapper.selectById(1L);
        assertNotNull(stored);
        assertEquals("云边端一体化智能算法应用平台", stored.getPlatformName());
        assertEquals("云边端一体算法预警监控平台", stored.getDashboardTitle());
        assertNull(stored.getPlatformLogoFileId());
        assertNull(response.getPlatformLogo());
    }

    @Test
    public void testSavePlatformBranding_preservesDatabaseDefaults() {
        PlatformBrandingDO config = new PlatformBrandingDO();
        config.setId(1L);
        config.setDefaultPlatformName("数据库初始平台");
        config.setDefaultDashboardTitle("数据库初始大屏");
        platformBrandingMapper.insert(config);

        platformBrandingService.savePlatformBranding(createSaveRequest());

        PlatformBrandingDO stored = platformBrandingMapper.selectById(1L);
        assertEquals("测试平台", stored.getPlatformName());
        assertEquals("数据库初始平台", stored.getDefaultPlatformName());
        assertEquals("数据库初始大屏", stored.getDefaultDashboardTitle());
    }

    @Test
    public void testResetPlatformBranding_usesAndPreservesDatabaseDefaults() {
        FileDO currentLogo = createImageFile("https://files.example.com/current-logo.webp");
        FileDO defaultLogo = createImageFile("https://files.example.com/default-logo.webp");
        PlatformBrandingDO config = new PlatformBrandingDO();
        config.setId(1L);
        config.setPlatformName("当前平台");
        config.setPlatformLogoFileId(currentLogo.getId());
        config.setDashboardTitle("当前大屏");
        config.setLoginName("当前登录页");
        config.setLoginFormTitle("当前登录标题");
        config.setDefaultPlatformName("数据库初始平台");
        config.setDefaultPlatformLogoFileId(defaultLogo.getId());
        config.setDefaultLoginName("数据库初始登录页");
        config.setDefaultLoginFormTitle("数据库初始登录标题");
        platformBrandingMapper.insert(config);

        PlatformBrandingRespVO response = platformBrandingService.resetPlatformBranding();

        PlatformBrandingDO stored = platformBrandingMapper.selectById(1L);
        assertEquals("数据库初始平台", stored.getPlatformName());
        assertEquals(defaultLogo.getId(), stored.getPlatformLogoFileId());
        assertEquals("云边端一体算法预警监控平台", stored.getDashboardTitle());
        assertEquals("数据库初始登录页", stored.getLoginName());
        assertEquals("数据库初始登录标题", stored.getLoginFormTitle());
        assertEquals("数据库初始平台", stored.getDefaultPlatformName());
        assertEquals(defaultLogo.getId(), stored.getDefaultPlatformLogoFileId());
        assertEquals(defaultLogo.getId(), response.getPlatformLogoFileId());
        assertEquals("/admin-api/infra/platform-branding/image/view?fileId=" + defaultLogo.getId(),
                response.getPlatformLogo());
    }

    private PlatformBrandingSaveReqVO createSaveRequest() {
        PlatformBrandingSaveReqVO request = new PlatformBrandingSaveReqVO();
        request.setPlatformName("测试平台");
        request.setDashboardTitle("测试大屏");
        request.setLoginName("测试登录页");
        request.setLoginFormTitle("");
        return request;
    }

    private FileDO createImageFile(String url) {
        FileDO file = new FileDO();
        file.setConfigId(1L);
        file.setName("branding.webp");
        file.setPath("branding/branding.webp");
        file.setUrl(url);
        file.setType("image/webp");
        file.setSize(1024);
        fileMapper.insert(file);
        return file;
    }
}
