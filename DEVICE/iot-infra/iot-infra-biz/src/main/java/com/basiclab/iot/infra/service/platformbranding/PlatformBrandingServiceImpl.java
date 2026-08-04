package com.basiclab.iot.infra.service.platformbranding;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingRespVO;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingSaveReqVO;
import com.basiclab.iot.infra.dal.dataobject.file.FileDO;
import com.basiclab.iot.infra.dal.dataobject.platformbranding.PlatformBrandingDO;
import com.basiclab.iot.infra.dal.pgsql.file.FileMapper;
import com.basiclab.iot.infra.dal.pgsql.platformbranding.PlatformBrandingMapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.sql.SQLException;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.infra.enums.ErrorCodeConstants.PLATFORM_BRANDING_IMAGE_NOT_EXISTS;
import static com.basiclab.iot.infra.enums.ErrorCodeConstants.PLATFORM_BRANDING_IMAGE_TYPE_INVALID;
import static com.basiclab.iot.infra.enums.ErrorCodeConstants.PLATFORM_BRANDING_TABLE_NOT_INITIALIZED;
import static com.basiclab.iot.infra.service.platformbranding.PlatformBrandingFileUrlBuilder.build;

/**
 * 平台品牌配置 Service 实现
 */
@Service
@Validated
public class PlatformBrandingServiceImpl implements PlatformBrandingService {

    private static final long GLOBAL_CONFIG_ID = 1L;
    private static final String DEFAULT_PLATFORM_NAME = "云边端一体化智能算法应用平台";
    private static final String DEFAULT_DASHBOARD_TITLE = "云边端一体算法预警监控平台";

    @Resource
    private PlatformBrandingMapper platformBrandingMapper;

    @Resource
    private FileMapper fileMapper;

    @Override
    public PlatformBrandingRespVO getPlatformBranding() {
        return buildResponse(platformBrandingMapper.selectById(GLOBAL_CONFIG_ID));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PlatformBrandingRespVO savePlatformBranding(PlatformBrandingSaveReqVO reqVO) {
        validateImageFile(reqVO.getPlatformLogoFileId());
        validateImageFile(reqVO.getLoginLogoFileId());
        validateImageFile(reqVO.getLoginBgLightFileId());
        validateImageFile(reqVO.getLoginBgDarkFileId());

        PlatformBrandingDO config = new PlatformBrandingDO();
        config.setId(GLOBAL_CONFIG_ID);
        config.setPlatformName(reqVO.getPlatformName().trim());
        config.setPlatformLogoFileId(reqVO.getPlatformLogoFileId());
        config.setDashboardTitle(reqVO.getDashboardTitle().trim());
        config.setLoginName(reqVO.getLoginName().trim());
        config.setLoginLogoFileId(reqVO.getLoginLogoFileId());
        config.setLoginFormTitle(reqVO.getLoginFormTitle() == null ? "" : reqVO.getLoginFormTitle().trim());
        config.setLoginBgLightFileId(reqVO.getLoginBgLightFileId());
        config.setLoginBgDarkFileId(reqVO.getLoginBgDarkFileId());
        upsert(config, false);
        return buildResponse(platformBrandingMapper.selectById(GLOBAL_CONFIG_ID));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PlatformBrandingRespVO resetPlatformBranding() {
        PlatformBrandingDO stored = selectStoredConfigForWrite();
        PlatformBrandingDO config = new PlatformBrandingDO();
        config.setId(GLOBAL_CONFIG_ID);
        config.setPlatformName(resolveInitialText(
                stored == null ? null : stored.getDefaultPlatformName(), DEFAULT_PLATFORM_NAME));
        config.setDashboardTitle(resolveInitialText(
                stored == null ? null : stored.getDefaultDashboardTitle(), DEFAULT_DASHBOARD_TITLE));
        config.setLoginName(resolveInitialText(
                stored == null ? null : stored.getDefaultLoginName(), DEFAULT_PLATFORM_NAME));
        config.setLoginFormTitle(resolveInitialOptionalText(
                stored == null ? null : stored.getDefaultLoginFormTitle(), ""));
        config.setPlatformLogoFileId(resolveInitialImageFileId(
                stored == null ? null : stored.getDefaultPlatformLogoFileId()));
        config.setLoginLogoFileId(resolveInitialImageFileId(
                stored == null ? null : stored.getDefaultLoginLogoFileId()));
        config.setLoginBgLightFileId(resolveInitialImageFileId(
                stored == null ? null : stored.getDefaultLoginBgLightFileId()));
        config.setLoginBgDarkFileId(resolveInitialImageFileId(
                stored == null ? null : stored.getDefaultLoginBgDarkFileId()));
        upsert(config, true);
        return buildResponse(platformBrandingMapper.selectById(GLOBAL_CONFIG_ID));
    }

    private void upsert(PlatformBrandingDO config, boolean overwriteImageFileIds) {
        try {
            if (platformBrandingMapper.selectById(GLOBAL_CONFIG_ID) == null) {
                platformBrandingMapper.insert(config);
                return;
            }
            if (overwriteImageFileIds) {
                LambdaUpdateWrapper<PlatformBrandingDO> updateWrapper = new LambdaUpdateWrapper<>();
                updateWrapper.eq(PlatformBrandingDO::getId, GLOBAL_CONFIG_ID)
                        .set(PlatformBrandingDO::getPlatformLogoFileId, config.getPlatformLogoFileId())
                        .set(PlatformBrandingDO::getLoginLogoFileId, config.getLoginLogoFileId())
                        .set(PlatformBrandingDO::getLoginBgLightFileId, config.getLoginBgLightFileId())
                        .set(PlatformBrandingDO::getLoginBgDarkFileId, config.getLoginBgDarkFileId());
                PlatformBrandingDO textConfig = new PlatformBrandingDO();
                textConfig.setId(config.getId());
                textConfig.setPlatformName(config.getPlatformName());
                textConfig.setDashboardTitle(config.getDashboardTitle());
                textConfig.setLoginName(config.getLoginName());
                textConfig.setLoginFormTitle(config.getLoginFormTitle());
                platformBrandingMapper.update(textConfig, updateWrapper);
                return;
            }
            platformBrandingMapper.updateById(config);
        } catch (DataAccessException error) {
            if (isUndefinedTable(error)) {
                throw exception(PLATFORM_BRANDING_TABLE_NOT_INITIALIZED);
            }
            throw error;
        }
    }

    private PlatformBrandingDO selectStoredConfigForWrite() {
        try {
            return platformBrandingMapper.selectById(GLOBAL_CONFIG_ID);
        } catch (DataAccessException error) {
            if (isUndefinedTable(error)) {
                throw exception(PLATFORM_BRANDING_TABLE_NOT_INITIALIZED);
            }
            throw error;
        }
    }

    private void validateImageFile(Long fileId) {
        if (fileId == null) {
            return;
        }
        FileDO file = fileMapper.selectById(fileId);
        if (file == null) {
            throw exception(PLATFORM_BRANDING_IMAGE_NOT_EXISTS);
        }
        if (file.getType() == null || !file.getType().startsWith("image/")) {
            throw exception(PLATFORM_BRANDING_IMAGE_TYPE_INVALID);
        }
    }

    private PlatformBrandingRespVO buildResponse(PlatformBrandingDO config) {
        PlatformBrandingRespVO response = new PlatformBrandingRespVO();
        if (config == null) {
            return response;
        }
        response.setPlatformName(resolveText(config.getPlatformName(),
                config.getDefaultPlatformName(), DEFAULT_PLATFORM_NAME));
        applyPlatformLogo(response, resolveImageFile(config.getPlatformLogoFileId(),
                config.getDefaultPlatformLogoFileId()));
        response.setDashboardTitle(resolveText(config.getDashboardTitle(),
                config.getDefaultDashboardTitle(), DEFAULT_DASHBOARD_TITLE));
        response.setLoginName(resolveText(config.getLoginName(),
                config.getDefaultLoginName(), DEFAULT_PLATFORM_NAME));
        applyLoginLogo(response, resolveImageFile(config.getLoginLogoFileId(),
                config.getDefaultLoginLogoFileId()));
        response.setLoginFormTitle(resolveOptionalText(config.getLoginFormTitle(),
                config.getDefaultLoginFormTitle(), ""));
        applyLoginBgLight(response, resolveImageFile(config.getLoginBgLightFileId(),
                config.getDefaultLoginBgLightFileId()));
        applyLoginBgDark(response, resolveImageFile(config.getLoginBgDarkFileId(),
                config.getDefaultLoginBgDarkFileId()));
        return response;
    }

    private String resolveText(String currentValue, String initialValue, String legacyValue) {
        if (StrUtil.isNotBlank(currentValue)) {
            return currentValue;
        }
        return resolveInitialText(initialValue, legacyValue);
    }

    private String resolveInitialText(String initialValue, String legacyValue) {
        return StrUtil.isNotBlank(initialValue) ? initialValue : legacyValue;
    }

    private String resolveOptionalText(String currentValue, String initialValue, String legacyValue) {
        if (currentValue != null) {
            return currentValue;
        }
        return resolveInitialOptionalText(initialValue, legacyValue);
    }

    private String resolveInitialOptionalText(String initialValue, String legacyValue) {
        return initialValue != null ? initialValue : legacyValue;
    }

    private Long resolveInitialImageFileId(Long fileId) {
        FileDO file = findImageFile(fileId);
        return file == null ? null : file.getId();
    }

    private FileDO resolveImageFile(Long currentFileId, Long initialFileId) {
        FileDO currentFile = findImageFile(currentFileId);
        return currentFile != null ? currentFile : findImageFile(initialFileId);
    }

    private FileDO findImageFile(Long fileId) {
        if (fileId == null) {
            return null;
        }
        FileDO file = fileMapper.selectById(fileId);
        if (file == null || file.getType() == null || !file.getType().startsWith("image/")) {
            return null;
        }
        return file;
    }

    private void applyPlatformLogo(PlatformBrandingRespVO response, FileDO file) {
        response.setPlatformLogoFileId(file == null ? null : file.getId());
        response.setPlatformLogo(file == null ? null : build(file));
    }

    private void applyLoginLogo(PlatformBrandingRespVO response, FileDO file) {
        response.setLoginLogoFileId(file == null ? null : file.getId());
        response.setLoginLogo(file == null ? null : build(file));
    }

    private void applyLoginBgLight(PlatformBrandingRespVO response, FileDO file) {
        response.setLoginBgLightFileId(file == null ? null : file.getId());
        response.setLoginBgLight(file == null ? null : build(file));
    }

    private void applyLoginBgDark(PlatformBrandingRespVO response, FileDO file) {
        response.setLoginBgDarkFileId(file == null ? null : file.getId());
        response.setLoginBgDark(file == null ? null : build(file));
    }

    private boolean isUndefinedTable(Throwable error) {
        Throwable current = error;
        while (current != null) {
            if (current instanceof SQLException && "42P01".equals(((SQLException) current).getSQLState())) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }
}
