package com.basiclab.iot.model.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelTypeDO;
import com.basiclab.iot.model.domain.model.vo.ModelTypePageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelTypeRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelTypeSaveReqVO;
import com.basiclab.iot.model.service.ModelTypeService;
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

@Tag(name = "管理后台 - 模型类型")
@RestController
@RequestMapping("/model/type")
@Validated
public class ModelTypeController {

    @Resource
    private ModelTypeService modelTypeService;

    @PostMapping("/create")
    @Operation(summary = "创建模型类型")
    //@PreAuthorize("@ss.hasPermission('model:type:create')")
    public CommonResult<Long> createModelType(@Valid @RequestBody ModelTypeSaveReqVO createReqVO) {
        return success(modelTypeService.createModelType(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型类型")
    //@PreAuthorize("@ss.hasPermission('model:type:update')")
    public CommonResult<Boolean> updateModelType(@Valid @RequestBody ModelTypeSaveReqVO updateReqVO) {
        modelTypeService.updateModelType(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型类型")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('model:type:delete')")
    public CommonResult<Boolean> deleteModelType(@RequestParam("id") Long id) {
        modelTypeService.deleteModelType(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型类型")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('model:type:query')")
    public CommonResult<ModelTypeRespVO> getModelType(@RequestParam("id") Long id) {
        ModelTypeDO type = modelTypeService.getModelType(id);
        return success(BeanUtils.toBean(type, ModelTypeRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型类型分页")
    //@PreAuthorize("@ss.hasPermission('model:type:query')")
    public CommonResult<PageResult<ModelTypeRespVO>> getModelTypePage(@Valid ModelTypePageReqVO pageReqVO) {
        PageResult<ModelTypeDO> pageResult = modelTypeService.getModelTypePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelTypeRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型类型 Excel")
    //@PreAuthorize("@ss.hasPermission('model:type:export')")
    // @ApiAccessLog(operateModelType = EXPORT)
    public void exportModelTypeExcel(@Valid ModelTypePageReqVO pageReqVO,
                                     HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelTypeDO> list = modelTypeService.getModelTypePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型类型.xls", "数据", ModelTypeRespVO.class,
                BeanUtils.toBean(list, ModelTypeRespVO.class));
    }

}