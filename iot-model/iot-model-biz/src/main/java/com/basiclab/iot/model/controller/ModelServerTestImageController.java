package com.basiclab.iot.model.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestImageDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImagePageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImageRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImageSaveReqVO;
import com.basiclab.iot.model.service.ModelServerTestImageService;
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

@Tag(name = "管理后台 - 模型测试图片")
@RestController
@RequestMapping("/model/server-test-image")
@Validated
public class ModelServerTestImageController {

    @Resource
    private ModelServerTestImageService serverTestImageService;

    @PostMapping("/create")
    @Operation(summary = "创建模型测试图片")
    //@PreAuthorize("@ss.hasPermission('model:server-test-image:create')")
    public CommonResult<Long> createServerTestImage(@Valid @RequestBody ModelServerTestImageSaveReqVO createReqVO) {
        return success(serverTestImageService.createModelServerTestImage(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型测试图片")
    //@PreAuthorize("@ss.hasPermission('model:server-test-image:update')")
    public CommonResult<Boolean> updateServerTestImage(@Valid @RequestBody ModelServerTestImageSaveReqVO updateReqVO) {
        serverTestImageService.updateModelServerTestImage(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型测试图片")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('model:server-test-image:delete')")
    public CommonResult<Boolean> deleteServerTestImage(@RequestParam("id") Long id) {
        serverTestImageService.deleteModelServerTestImage(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型测试图片")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('model:server-test-image:query')")
    public CommonResult<ModelServerTestImageRespVO> getServerTestImage(@RequestParam("id") Long id) {
        ModelServerTestImageDO serverTestImage = serverTestImageService.getModelServerTestImage(id);
        return success(BeanUtils.toBean(serverTestImage, ModelServerTestImageRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型测试图片分页")
    //@PreAuthorize("@ss.hasPermission('model:server-test-image:query')")
    public CommonResult<PageResult<ModelServerTestImageRespVO>> getServerTestImagePage(@Valid ModelServerTestImagePageReqVO pageReqVO) {
        PageResult<ModelServerTestImageDO> pageResult = serverTestImageService.getModelServerTestImagePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelServerTestImageRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型测试图片 Excel")
    //@PreAuthorize("@ss.hasPermission('model:server-test-image:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportServerTestImageExcel(@Valid ModelServerTestImagePageReqVO pageReqVO,
                                           HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelServerTestImageDO> list = serverTestImageService.getModelServerTestImagePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型测试图片.xls", "数据", ModelServerTestImageRespVO.class,
                BeanUtils.toBean(list, ModelServerTestImageRespVO.class));
    }

}