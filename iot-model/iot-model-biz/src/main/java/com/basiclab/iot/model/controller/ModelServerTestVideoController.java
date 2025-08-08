package com.basiclab.iot.model.controller;

import com.basiclab.iot.model.dal.dataobject.ModelServerTestVideoDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoSaveReqVO;
import com.basiclab.iot.model.service.ModelServerTestVideoService;
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

@Tag(name = "管理后台 - 模型测试视频")
@RestController
@RequestMapping("/model/server-test-video")
@Validated
public class ModelServerTestVideoController {

    @Resource
    private ModelServerTestVideoService modelServerTestVideoService;

    @PostMapping("/create")
    @Operation(summary = "创建模型测试视频")
    // @PreAuthorize("@ss.hasPermission('model:server-test-video:create')")
    public CommonResult<Long> createModelServerTestVideo(@Valid @RequestBody ModelServerTestVideoSaveReqVO createReqVO) {
        return success(modelServerTestVideoService.createModelServerTestVideo(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型测试视频")
    // @PreAuthorize("@ss.hasPermission('model:server-test-video:update')")
    public CommonResult<Boolean> updateModelServerTestVideo(@Valid @RequestBody ModelServerTestVideoSaveReqVO updateReqVO) {
        modelServerTestVideoService.updateModelServerTestVideo(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型测试视频")
    @Parameter(name = "id", description = "编号", required = true)
    // @PreAuthorize("@ss.hasPermission('model:server-test-video:delete')")
    public CommonResult<Boolean> deleteModelServerTestVideo(@RequestParam("id") Long id) {
        modelServerTestVideoService.deleteModelServerTestVideo(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型测试视频")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    // @PreAuthorize("@ss.hasPermission('model:server-test-video:query')")
    public CommonResult<ModelServerTestVideoRespVO> getModelServerTestVideo(@RequestParam("id") Long id) {
        ModelServerTestVideoDO serverTestVideo = modelServerTestVideoService.getModelServerTestVideo(id);
        return success(BeanUtils.toBean(serverTestVideo, ModelServerTestVideoRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型测试视频分页")
    // @PreAuthorize("@ss.hasPermission('model:server-test-video:query')")
    public CommonResult<PageResult<ModelServerTestVideoRespVO>> getModelServerTestVideoPage(@Valid ModelServerTestVideoPageReqVO pageReqVO) {
        PageResult<ModelServerTestVideoDO> pageResult = modelServerTestVideoService.getModelServerTestVideoPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelServerTestVideoRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型测试视频 Excel")
    // @PreAuthorize("@ss.hasPermission('model:server-test-video:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportModelServerTestVideoExcel(@Valid ModelServerTestVideoPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelServerTestVideoDO> list = modelServerTestVideoService.getModelServerTestVideoPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型测试视频.xls", "数据", ModelServerTestVideoRespVO.class,
                        BeanUtils.toBean(list, ModelServerTestVideoRespVO.class));
    }

}