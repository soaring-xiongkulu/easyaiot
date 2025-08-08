package com.basiclab.iot.model.controller;

import com.basiclab.iot.model.dal.dataobject.ModelServerQuantifyDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifyPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifyRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifySaveReqVO;
import com.basiclab.iot.model.service.ModelServerQuantifyService;
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

@Tag(name = "管理后台 - 模型量化服务")
@RestController
@RequestMapping("/model/server-quantify")
@Validated
public class ModelServerQuantifyController {

    @Resource
    private ModelServerQuantifyService modelServerQuantifyService;

    @PostMapping("/create")
    @Operation(summary = "创建模型量化服务")
    // @PreAuthorize("@ss.hasPermission('model:server-quantify:create')")
    public CommonResult<Long> createModelServerQuantify(@Valid @RequestBody ModelServerQuantifySaveReqVO createReqVO) {
        return success(modelServerQuantifyService.createServerQuantify(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型量化服务")
    // @PreAuthorize("@ss.hasPermission('model:server-quantify:update')")
    public CommonResult<Boolean> updateModelServerQuantify(@Valid @RequestBody ModelServerQuantifySaveReqVO updateReqVO) {
        modelServerQuantifyService.updateServerQuantify(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型量化服务")
    @Parameter(name = "id", description = "编号", required = true)
    // @PreAuthorize("@ss.hasPermission('model:server-quantify:delete')")
    public CommonResult<Boolean> deleteModelServerQuantify(@RequestParam("id") Long id) {
        modelServerQuantifyService.deleteServerQuantify(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型量化服务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    // @PreAuthorize("@ss.hasPermission('model:server-quantify:query')")
    public CommonResult<ModelServerQuantifyRespVO> getModelServerQuantify(@RequestParam("id") Long id) {
        ModelServerQuantifyDO serverQuantify = modelServerQuantifyService.getServerQuantify(id);
        return success(BeanUtils.toBean(serverQuantify, ModelServerQuantifyRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型量化服务分页")
    // @PreAuthorize("@ss.hasPermission('model:server-quantify:query')")
    public CommonResult<PageResult<ModelServerQuantifyRespVO>> getModelServerQuantifyPage(@Valid ModelServerQuantifyPageReqVO pageReqVO) {
        PageResult<ModelServerQuantifyDO> pageResult = modelServerQuantifyService.getServerQuantifyPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelServerQuantifyRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型量化服务 Excel")
    // @PreAuthorize("@ss.hasPermission('model:server-quantify:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportModelServerQuantifyExcel(@Valid ModelServerQuantifyPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelServerQuantifyDO> list = modelServerQuantifyService.getServerQuantifyPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型量化服务.xls", "数据", ModelServerQuantifyRespVO.class,
                        BeanUtils.toBean(list, ModelServerQuantifyRespVO.class));
    }

}