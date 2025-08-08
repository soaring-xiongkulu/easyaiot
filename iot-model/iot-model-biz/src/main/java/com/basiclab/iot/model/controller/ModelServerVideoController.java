package com.basiclab.iot.model.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerVideoDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoRespVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoSaveReqVO;
import com.basiclab.iot.model.service.ModelServerVideoService;
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

@Tag(name = "管理后台 - 模型服务视频")
@RestController
@RequestMapping("/model/server-video")
@Validated
public class ModelServerVideoController {

    @Resource
    private ModelServerVideoService modelServerVideoService;

    @PostMapping("/create")
    @Operation(summary = "创建模型服务视频")
    //@PreAuthorize("@ss.hasPermission('model:server-video:create')")
    public CommonResult<Long> createModelServerVideo(@Valid @RequestBody ModelServerVideoSaveReqVO createReqVO) {
        return success(modelServerVideoService.createModelServerVideo(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新模型服务视频")
    //@PreAuthorize("@ss.hasPermission('model:server-video:update')")
    public CommonResult<Boolean> updateModelServerVideo(@Valid @RequestBody ModelServerVideoSaveReqVO updateReqVO) {
        modelServerVideoService.updateModelServerVideo(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除模型服务视频")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('model:server-video:delete')")
    public CommonResult<Boolean> deleteModelServerVideo(@RequestParam("id") Long id) {
        modelServerVideoService.deleteModelServerVideo(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得模型服务视频")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('model:server-video:query')")
    public CommonResult<ModelServerVideoRespVO> getModelServerVideo(@RequestParam("id") Long id) {
        ModelServerVideoDO serverVideo = modelServerVideoService.getModelServerVideo(id);
        return success(BeanUtils.toBean(serverVideo, ModelServerVideoRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得模型服务视频分页")
    //@PreAuthorize("@ss.hasPermission('model:server-video:query')")
    public CommonResult<PageResult<ModelServerVideoRespVO>> getModelServerVideoPage(@Valid ModelServerVideoPageReqVO pageReqVO) {
        PageResult<ModelServerVideoDO> pageResult = modelServerVideoService.getModelServerVideoPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ModelServerVideoRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出模型服务视频 Excel")
    //@PreAuthorize("@ss.hasPermission('model:server-video:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportModelServerVideoExcel(@Valid ModelServerVideoPageReqVO pageReqVO,
                                            HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ModelServerVideoDO> list = modelServerVideoService.getModelServerVideoPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "模型服务视频.xls", "数据", ModelServerVideoRespVO.class,
                BeanUtils.toBean(list, ModelServerVideoRespVO.class));
    }

}