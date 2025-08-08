package com.basiclab.iot.dataset.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDatasetDO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetPageReqVO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetRespVO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetSaveReqVO;
import com.basiclab.iot.dataset.service.WarehouseDatasetService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;


@Tag(name = "管理后台 - 数据仓数据集关联")
@RestController
@RequestMapping("/warehouse/dataset")
@Validated
public class WarehouseDatasetController {

    @Resource
    private WarehouseDatasetService warehouseDatasetService;

    @PostMapping("/create")
    @Operation(summary = "创建数据仓数据集关联")
    // @PreAuthorize("@ss.hasPermission('warehouse:dataset:create')")
    public CommonResult<Long> createWarehouseDataset(@Valid @RequestBody WarehouseDatasetSaveReqVO createReqVO) {
        return success(warehouseDatasetService.createWarehouseDataset(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新数据仓数据集关联")
    // @PreAuthorize("@ss.hasPermission('warehouse:dataset:update')")
    public CommonResult<Boolean> updateWarehouseDataset(@Valid @RequestBody WarehouseDatasetSaveReqVO updateReqVO) {
        warehouseDatasetService.updateWarehouseDataset(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除数据仓数据集关联")
    @Parameter(name = "id", description = "编号", required = true)
    // @PreAuthorize("@ss.hasPermission('warehouse:dataset:delete')")
    public CommonResult<Boolean> deleteWarehouseDataset(@RequestParam("id") Long id) {
        warehouseDatasetService.deleteWarehouseDataset(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得数据仓数据集关联")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    // @PreAuthorize("@ss.hasPermission('warehouse:dataset:query')")
    public CommonResult<WarehouseDatasetRespVO> getWarehouseDataset(@RequestParam("id") Long id) {
        WarehouseDatasetDO dataset = warehouseDatasetService.getWarehouseDataset(id);
        return success(BeanUtils.toBean(dataset, WarehouseDatasetRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得数据仓数据集关联分页")
    // @PreAuthorize("@ss.hasPermission('warehouse:dataset:query')")
    public CommonResult<PageResult<WarehouseDatasetRespVO>> getWarehouseDatasetPage(@Valid WarehouseDatasetPageReqVO pageReqVO) {
        PageResult<WarehouseDatasetDO> pageResult = warehouseDatasetService.getWarehouseDatasetPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, WarehouseDatasetRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出数据仓数据集关联 Excel")
    // @PreAuthorize("@ss.hasPermission('warehouse:dataset:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportWarehouseDatasetExcel(@Valid WarehouseDatasetPageReqVO pageReqVO,
                                            HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<WarehouseDatasetDO> list = warehouseDatasetService.getWarehouseDatasetPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "数据仓数据集关联.xls", "数据", WarehouseDatasetRespVO.class,
                BeanUtils.toBean(list, WarehouseDatasetRespVO.class));
    }

}