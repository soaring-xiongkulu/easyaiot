package com.basiclab.iot.dataset.controller;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetVideoDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetVideoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * DatasetVideoController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 视频数据集")
@RestController
@RequestMapping("/dataset/video")
@Validated
public class DatasetVideoController {

    @Resource
    private DatasetVideoService datasetVideoService;

    @PostMapping("/create")
    @Operation(summary = "创建视频数据集")
    //@PreAuthorize("@ss.hasPermission('dataset:video:create')")
    public CommonResult<Long> createDatasetVideo(@Valid @RequestBody DatasetVideoSaveReqVO createReqVO) {
        return success(datasetVideoService.createDatasetVideo(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新视频数据集")
    //@PreAuthorize("@ss.hasPermission('dataset:video:update')")
    public CommonResult<Boolean> updateDatasetVideo(@Valid @RequestBody DatasetVideoSaveReqVO updateReqVO) {
        datasetVideoService.updateDatasetVideo(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除视频数据集")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:video:delete')")
    public CommonResult<Boolean> deleteDatasetVideo(@RequestParam("id") Long id) {
        datasetVideoService.deleteDatasetVideo(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得视频数据集")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:video:query')")
    public CommonResult<DatasetVideoRespVO> getDatasetVideo(@RequestParam("id") Long id) {
        DatasetVideoDO video = datasetVideoService.getDatasetVideo(id);
        return success(BeanUtils.toBean(video, DatasetVideoRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得视频数据集分页")
    //@PreAuthorize("@ss.hasPermission('dataset:video:query')")
    public CommonResult<PageResult<DatasetVideoRespVO>> getDatasetVideoPage(@Valid DatasetVideoPageReqVO pageReqVO) {
        PageResult<DatasetVideoDO> pageResult = datasetVideoService.getDatasetVideoPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetVideoRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出视频数据集 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:video:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetVideoExcel(@Valid DatasetVideoPageReqVO pageReqVO,
                                        HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetVideoDO> list = datasetVideoService.getDatasetVideoPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "视频数据集.xls", "数据", DatasetVideoRespVO.class,
                BeanUtils.toBean(list, DatasetVideoRespVO.class));
    }

}