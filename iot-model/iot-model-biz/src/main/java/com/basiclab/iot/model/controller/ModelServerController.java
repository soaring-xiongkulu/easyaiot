package com.basiclab.iot.model.controller;

import com.basiclab.iot.model.dal.dataobject.ModelServerDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerSaveReqVO;
import com.basiclab.iot.model.service.ModelServerService;
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

import com.basiclab.iot.common.excels.core.util.ExcelUtils;


@Tag(name = "管理后台 - 模型服务")
@RestController
@RequestMapping("/model/server")
@Validated
public class ModelServerController {

    @Resource
    private ModelServerService serverService;

    @PostMapping("/create")
    @Operation(summary = "创建模型服务")
    //@PreAuthorize("@ss.hasPermission('model:server:create')")
    public CommonResult<Long> createServer(@Valid @RequestBody ModelServerSaveReqVO createReqVO) {
        return success(serverService.createServer(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型服务")
    //@PreAuthorize("@ss.hasPermission('model:server:update')")
    public CommonResult<Boolean> updateServer(@Valid @RequestBody ModelServerSaveReqVO updateReqVO) {
        serverService.updateServer(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型服务")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('model:server:delete')")
    public CommonResult<Boolean> deleteServer(@RequestParam("id") Long id) {
        serverService.deleteServer(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型服务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('model:server:query')")
    public CommonResult<ModelServerRespVO> getServer(@RequestParam("id") Long id) {
        ModelServerDO server = serverService.getServer(id);
        return success(BeanUtils.toBean(server, ModelServerRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型服务分页")
    //@PreAuthorize("@ss.hasPermission('model:server:query')")
    public CommonResult<PageResult<ModelServerRespVO>> getServerPage(@Valid ModelServerPageReqVO pageReqVO) {
        PageResult<ModelServerDO> pageResult = serverService.getServerPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelServerRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型服务 Excel")
    //@PreAuthorize("@ss.hasPermission('model:server:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportServerExcel(@Valid ModelServerPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelServerDO> list = serverService.getServerPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型服务.xls", "数据", ModelServerRespVO.class,
                        BeanUtils.toBean(list, ModelServerRespVO.class));
    }

}