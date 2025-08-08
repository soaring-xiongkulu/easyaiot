package com.basiclab.iot.model.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestSaveReqVO;
import com.basiclab.iot.model.service.ModelServerTestService;
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

@Tag(name = "管理后台 - 模型测试服务")
@RestController
@RequestMapping("/model/server-test")
@Validated
public class ModelServerTestController {

    @Resource
    private ModelServerTestService modelServerTestService;

    @PostMapping("/create")
    @Operation(summary = "创建模型测试服务")
    //@PreAuthorize("@ss.hasPermission('model:server-test:create')")
    public CommonResult<Long> createModelServerTest(@Valid @RequestBody ModelServerTestSaveReqVO createReqVO) {
        return success(modelServerTestService.createModelServerTest(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型测试服务")
    //@PreAuthorize("@ss.hasPermission('model:server-test:update')")
    public CommonResult<Boolean> updateModelServerTest(@Valid @RequestBody ModelServerTestSaveReqVO updateReqVO) {
        modelServerTestService.updateModelServerTest(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型测试服务")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('model:server-test:delete')")
    public CommonResult<Boolean> deleteModelServerTest(@RequestParam("id") Long id) {
        modelServerTestService.deleteModelServerTest(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型测试服务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('model:server-test:query')")
    public CommonResult<ModelServerTestRespVO> getModelServerTest(@RequestParam("id") Long id) {
        ModelServerTestDO serverTest = modelServerTestService.getModelServerTest(id);
        return success(BeanUtils.toBean(serverTest, ModelServerTestRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型测试服务分页")
    //@PreAuthorize("@ss.hasPermission('model:server-test:query')")
    public CommonResult<PageResult<ModelServerTestRespVO>> getModelServerTestPage(@Valid ModelServerTestPageReqVO pageReqVO) {
        PageResult<ModelServerTestDO> pageResult = modelServerTestService.getModelServerTestPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelServerTestRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型测试服务 Excel")
    //@PreAuthorize("@ss.hasPermission('model:server-test:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportModelServerTestExcel(@Valid ModelServerTestPageReqVO pageReqVO,
                                           HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelServerTestDO> list = modelServerTestService.getModelServerTestPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型测试服务.xls", "数据", ModelServerTestRespVO.class,
                BeanUtils.toBean(list, ModelServerTestRespVO.class));
    }

}