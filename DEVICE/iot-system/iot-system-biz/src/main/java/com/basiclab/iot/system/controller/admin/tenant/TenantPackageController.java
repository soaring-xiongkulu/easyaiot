package com.basiclab.iot.system.controller.admin.tenant;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.enums.CommonStatusEnum;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.system.controller.admin.tenant.vo.packages.TenantPackagePageReqVO;
import com.basiclab.iot.system.controller.admin.tenant.vo.packages.TenantPackageRespVO;
import com.basiclab.iot.system.controller.admin.tenant.vo.packages.TenantPackageSaveReqVO;
import com.basiclab.iot.system.controller.admin.tenant.vo.packages.TenantPackageSimpleRespVO;
import com.basiclab.iot.system.dal.dataobject.tenant.TenantPackageDO;
import com.basiclab.iot.system.service.tenant.TenantPackageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * TenantPackageController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 租户套餐")
@RestController
@RequestMapping("/system/tenant-package")
@Validated
public class TenantPackageController {

    @Resource
    private TenantPackageService tenantPackageService;

    @PostMapping("/create")
    @Operation(summary = "创建租户套餐")
    //@PreAuthorize("@ss.hasPermission('system:tenant-package:create')")
    public CommonResult<Long> createTenantPackage(@Valid @RequestBody TenantPackageSaveReqVO createReqVO) {
        return success(tenantPackageService.createTenantPackage(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新租户套餐")
    //@PreAuthorize("@ss.hasPermission('system:tenant-package:update')")
    public CommonResult<Boolean> updateTenantPackage(@Valid @RequestBody TenantPackageSaveReqVO updateReqVO) {
        tenantPackageService.updateTenantPackage(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除租户套餐")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('system:tenant-package:delete')")
    public CommonResult<Boolean> deleteTenantPackage(@RequestParam("id") Long id) {
        tenantPackageService.deleteTenantPackage(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得租户套餐")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('system:tenant-package:query')")
    public CommonResult<TenantPackageRespVO> getTenantPackage(@RequestParam("id") Long id) {
        TenantPackageDO tenantPackage = tenantPackageService.getTenantPackage(id);
        return success(BeanUtils.toBean(tenantPackage, TenantPackageRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得租户套餐分页")
    //@PreAuthorize("@ss.hasPermission('system:tenant-package:query')")
    public CommonResult<PageResult<TenantPackageRespVO>> getTenantPackagePage(@Valid TenantPackagePageReqVO pageVO) {
        PageResult<TenantPackageDO> pageResult = tenantPackageService.getTenantPackagePage(pageVO);
        return success(BeanUtils.toBean(pageResult, TenantPackageRespVO.class));
    }

    @GetMapping({"/get-simple-list", "simple-list"})
    @Operation(summary = "获取租户套餐精简信息列表", description = "只包含被开启的租户套餐，主要用于前端的下拉选项")
    public CommonResult<List<TenantPackageSimpleRespVO>> getTenantPackageList() {
        List<TenantPackageDO> list = tenantPackageService.getTenantPackageListByStatus(CommonStatusEnum.ENABLE.getStatus());
        return success(BeanUtils.toBean(list, TenantPackageSimpleRespVO.class));
    }

}
