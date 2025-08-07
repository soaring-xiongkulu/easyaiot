package com.basiclab.iot.device.controller.admin.ota_packages;

import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;
import org.springframework.security.access.prepost.PreAuthorize;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Operation;

import javax.validation.*;
import javax.servlet.http.*;
import java.util.*;
import java.io.IOException;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import static com.basiclab.iot.common.domain.CommonResult.success;

import com.basiclab.iot.common.excel.core.util.ExcelUtils;

import com.basiclab.iot.common.apilog.core.annotation.ApiAccessLog;
import static com.basiclab.iot.common.apilog.core.enums.OperateTypeEnum.*;

import com.basiclab.iot.device.controller.admin.ota_packages.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_packages.OtaPackagesDO;
import com.basiclab.iot.device.service.ota_packages.OtaPackagesService;

@Tag(name = "管理后台 - OTA升级包")
@RestController
@RequestMapping("/ota/packages")
@Validated
public class OtaPackagesController {

    @Resource
    private OtaPackagesService packagesService;

    @PostMapping("/create")
    @Operation(summary = "创建OTA升级包")
    @PreAuthorize("@ss.hasPermission('ota:packages:create')")
    public CommonResult<Long> createPackages(@Valid @RequestBody OtaPackagesSaveReqVO createReqVO) {
        return success(packagesService.createPackages(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新OTA升级包")
    @PreAuthorize("@ss.hasPermission('ota:packages:update')")
    public CommonResult<Boolean> updatePackages(@Valid @RequestBody OtaPackagesSaveReqVO updateReqVO) {
        packagesService.updatePackages(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除OTA升级包")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('ota:packages:delete')")
    public CommonResult<Boolean> deletePackages(@RequestParam("id") Long id) {
        packagesService.deletePackages(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得OTA升级包")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('ota:packages:query')")
    public CommonResult<OtaPackagesRespVO> getPackages(@RequestParam("id") Long id) {
        OtaPackagesDO packages = packagesService.getPackages(id);
        return success(BeanUtils.toBean(packages, OtaPackagesRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得OTA升级包分页")
    @PreAuthorize("@ss.hasPermission('ota:packages:query')")
    public CommonResult<PageResult<OtaPackagesRespVO>> getPackagesPage(@Valid OtaPackagesPageReqVO pageReqVO) {
        PageResult<OtaPackagesDO> pageResult = packagesService.getPackagesPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, OtaPackagesRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出OTA升级包 Excel")
    @PreAuthorize("@ss.hasPermission('ota:packages:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportPackagesExcel(@Valid OtaPackagesPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<OtaPackagesDO> list = packagesService.getPackagesPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "OTA升级包.xls", "数据", OtaPackagesRespVO.class,
                        BeanUtils.toBean(list, OtaPackagesRespVO.class));
    }

}