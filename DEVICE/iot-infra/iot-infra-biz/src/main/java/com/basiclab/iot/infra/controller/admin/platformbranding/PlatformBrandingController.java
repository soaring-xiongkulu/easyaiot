package com.basiclab.iot.infra.controller.admin.platformbranding;

import cn.hutool.core.io.IoUtil;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingImageRespVO;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingRespVO;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingSaveReqVO;
import com.basiclab.iot.infra.dal.dataobject.file.FileDO;
import com.basiclab.iot.infra.service.file.FileService;
import com.basiclab.iot.infra.service.platformbranding.PlatformBrandingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.annotation.security.PermitAll;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;

import static com.basiclab.iot.common.domain.CommonResult.success;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.infra.enums.ErrorCodeConstants.PLATFORM_BRANDING_IMAGE_TYPE_INVALID;
import static com.basiclab.iot.infra.enums.ErrorCodeConstants.PLATFORM_BRANDING_IMAGE_NOT_EXISTS;
import static com.basiclab.iot.infra.service.platformbranding.PlatformBrandingFileUrlBuilder.build;

/**
 * 全平台品牌配置 Controller
 */
@Tag(name = "管理后台 - 平台品牌配置")
@RestController
@RequestMapping("/infra/platform-branding")
@Validated
public class PlatformBrandingController {

    private static final long MAX_IMAGE_SIZE = 3L * 1024 * 1024;

    @Resource
    private PlatformBrandingService platformBrandingService;

    @Resource
    private FileService fileService;

    @GetMapping("/get")
    @PermitAll
    @Operation(summary = "获取全平台品牌配置")
    public CommonResult<PlatformBrandingRespVO> getPlatformBranding() {
        return success(platformBrandingService.getPlatformBranding());
    }

    @GetMapping("/image/view")
    @PermitAll
    @Operation(summary = "读取平台品牌图片")
    public void getImage(@RequestParam("fileId") Long fileId,
                         HttpServletResponse response) throws Exception {
        FileDO file = fileService.getFile(fileId);
        if (file == null) {
            throw exception(PLATFORM_BRANDING_IMAGE_NOT_EXISTS);
        }
        if (file.getType() == null || !file.getType().startsWith("image/")) {
            throw exception(PLATFORM_BRANDING_IMAGE_TYPE_INVALID);
        }
        byte[] content = fileService.getFileContent(file.getConfigId(), file.getPath());
        if (content == null) {
            response.setStatus(HttpStatus.NOT_FOUND.value());
            return;
        }
        // 品牌图片用于 img、背景图和 favicon，必须以内联资源返回，不能携带附件下载响应头。
        response.setContentType(file.getType());
        response.setContentLength(content.length);
        IoUtil.write(response.getOutputStream(), false, content);
    }

    @PutMapping("/update")
    @PreAuthorize("@ss.hasAnyRoles('super_admin', 'tenant_admin', 'admin')")
    @Operation(summary = "保存全平台品牌配置")
    public CommonResult<PlatformBrandingRespVO> updatePlatformBranding(
            @Valid @RequestBody PlatformBrandingSaveReqVO reqVO) {
        return success(platformBrandingService.savePlatformBranding(reqVO));
    }

    @PostMapping("/reset")
    @PreAuthorize("@ss.hasAnyRoles('super_admin', 'tenant_admin', 'admin')")
    @Operation(summary = "重置并持久化全平台品牌配置")
    public CommonResult<PlatformBrandingRespVO> resetPlatformBranding() {
        return success(platformBrandingService.resetPlatformBranding());
    }

    @PostMapping("/image")
    @PreAuthorize("@ss.hasAnyRoles('super_admin', 'tenant_admin', 'admin')")
    @Operation(summary = "上传平台品牌图片")
    public CommonResult<PlatformBrandingImageRespVO> uploadImage(
            @RequestParam("file") MultipartFile file) throws Exception {
        if (file == null || file.isEmpty() || file.getSize() > MAX_IMAGE_SIZE
                || file.getContentType() == null || !file.getContentType().startsWith("image/")) {
            throw exception(PLATFORM_BRANDING_IMAGE_TYPE_INVALID);
        }
        FileDO savedFile = fileService.createFileRecord(file.getOriginalFilename(), null,
                IoUtil.readBytes(file.getInputStream()));
        return success(new PlatformBrandingImageRespVO(savedFile.getId(), build(savedFile)));
    }
}
