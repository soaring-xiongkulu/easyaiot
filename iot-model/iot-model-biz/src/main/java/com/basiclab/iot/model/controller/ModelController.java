package com.basiclab.iot.model.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelDO;
import com.basiclab.iot.model.domain.model.vo.ModelPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelSaveReqVO;
import com.basiclab.iot.model.service.ModelService;
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


@Tag(name = "管理后台 - 模型")
@RestController
@RequestMapping("/model/")
@Validated
public class ModelController {

    @Resource
    private ModelService modelService;

    @PostMapping("/create")
    @Operation(summary = "创建模型")
    // @PreAuthorize("@ss.hasPermission('model::create')")
    public CommonResult<Long> create(@Valid @RequestBody ModelSaveReqVO createReqVO) {
        return success(modelService.createModel(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型")
    // @PreAuthorize("@ss.hasPermission('model::update')")
    public CommonResult<Boolean> update(@Valid @RequestBody ModelSaveReqVO updateReqVO) {
        modelService.updateModel(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型")
    @Parameter(name = "id", description = "编号", required = true)
    // @PreAuthorize("@ss.hasPermission('model::delete')")
    public CommonResult<Boolean> delete(@RequestParam("id") Long id) {
        modelService.deleteModel(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    // @PreAuthorize("@ss.hasPermission('model::query')")
    public CommonResult<ModelRespVO> get(@RequestParam("id") Long id) {
        ModelDO model = modelService.getModel(id);
        return success(BeanUtils.toBean(model, ModelRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型分页")
    // @PreAuthorize("@ss.hasPermission('model::query')")
    public CommonResult<PageResult<ModelRespVO>> getPage(@Valid ModelPageReqVO ModelPageReqVO) {
        PageResult<ModelDO> pageResult = modelService.getModelPage(ModelPageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型 Excel")
    // @PreAuthorize("@ss.hasPermission('model::export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportExcel(@Valid ModelPageReqVO ModelPageReqVO,
                            HttpServletResponse response) throws IOException {
        ModelPageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelDO> list = modelService.getModelPage(ModelPageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型.xls", "数据", ModelRespVO.class,
                BeanUtils.toBean(list, ModelRespVO.class));
    }

}