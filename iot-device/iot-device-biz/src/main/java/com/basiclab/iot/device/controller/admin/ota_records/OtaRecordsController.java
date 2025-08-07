package com.basiclab.iot.device.controller.admin.ota_records;

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

import com.basiclab.iot.device.controller.admin.ota_records.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_records.OtaRecordsDO;
import com.basiclab.iot.device.service.ota_records.OtaRecordsService;

@Tag(name = "管理后台 - OTA升级记录")
@RestController
@RequestMapping("/ota/records")
@Validated
public class OtaRecordsController {

    @Resource
    private OtaRecordsService recordsService;

    @PostMapping("/create")
    @Operation(summary = "创建OTA升级记录")
    @PreAuthorize("@ss.hasPermission('ota:records:create')")
    public CommonResult<Long> createRecords(@Valid @RequestBody OtaRecordsSaveReqVO createReqVO) {
        return success(recordsService.createRecords(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新OTA升级记录")
    @PreAuthorize("@ss.hasPermission('ota:records:update')")
    public CommonResult<Boolean> updateRecords(@Valid @RequestBody OtaRecordsSaveReqVO updateReqVO) {
        recordsService.updateRecords(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除OTA升级记录")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('ota:records:delete')")
    public CommonResult<Boolean> deleteRecords(@RequestParam("id") Long id) {
        recordsService.deleteRecords(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得OTA升级记录")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('ota:records:query')")
    public CommonResult<OtaRecordsRespVO> getRecords(@RequestParam("id") Long id) {
        OtaRecordsDO records = recordsService.getRecords(id);
        return success(BeanUtils.toBean(records, OtaRecordsRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得OTA升级记录分页")
    @PreAuthorize("@ss.hasPermission('ota:records:query')")
    public CommonResult<PageResult<OtaRecordsRespVO>> getRecordsPage(@Valid OtaRecordsPageReqVO pageReqVO) {
        PageResult<OtaRecordsDO> pageResult = recordsService.getRecordsPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, OtaRecordsRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出OTA升级记录 Excel")
    @PreAuthorize("@ss.hasPermission('ota:records:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportRecordsExcel(@Valid OtaRecordsPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<OtaRecordsDO> list = recordsService.getRecordsPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "OTA升级记录.xls", "数据", OtaRecordsRespVO.class,
                        BeanUtils.toBean(list, OtaRecordsRespVO.class));
    }

}