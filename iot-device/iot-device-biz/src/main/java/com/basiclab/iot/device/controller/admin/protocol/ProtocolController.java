package com.basiclab.iot.device.controller.admin.protocol;

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

import com.basiclab.iot.device.controller.admin.protocol.vo.*;
import com.basiclab.iot.device.dal.dataobject.protocol.ProtocolDO;
import com.basiclab.iot.device.service.protocol.ProtocolService;

@Tag(name = "管理后台 - 协议信息")
@RestController
@RequestMapping("/protocol/")
@Validated
public class ProtocolController {

    @Resource
    private ProtocolService protocolService;

    @PostMapping("/create")
    @Operation(summary = "创建协议信息")
    @PreAuthorize("@ss.hasPermission('protocol::create')")
    public CommonResult<Long> create(@Valid @RequestBody ProtocolSaveReqVO createReqVO) {
        return success(protocolService.create(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新协议信息")
    @PreAuthorize("@ss.hasPermission('protocol::update')")
    public CommonResult<Boolean> update(@Valid @RequestBody ProtocolSaveReqVO updateReqVO) {
        protocolService.update(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除协议信息")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('protocol::delete')")
    public CommonResult<Boolean> delete(@RequestParam("id") Long id) {
        protocolService.delete(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得协议信息")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('protocol::query')")
    public CommonResult<ProtocolRespVO> get(@RequestParam("id") Long id) {
        ProtocolDO protocolDO = protocolService.get(id);
        return success(BeanUtils.toBean(protocolDO, ProtocolRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得协议信息分页")
    @PreAuthorize("@ss.hasPermission('protocol::query')")
    public CommonResult<PageResult<ProtocolRespVO>> getPage(@Valid ProtocolPageReqVO pageReqVO) {
        PageResult<ProtocolDO> pageResult = protocolService.getPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProtocolRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出协议信息 Excel")
    @PreAuthorize("@ss.hasPermission('protocol::export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportExcel(@Valid ProtocolPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProtocolDO> list = protocolService.getPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "协议信息.xls", "数据", ProtocolRespVO.class,
                        BeanUtils.toBean(list, ProtocolRespVO.class));
    }

}