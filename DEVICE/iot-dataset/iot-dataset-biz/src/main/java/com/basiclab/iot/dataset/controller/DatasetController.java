package com.basiclab.iot.dataset.controller;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetDO;
import com.basiclab.iot.dataset.domain.dataset.vo.*;
import com.basiclab.iot.dataset.service.DatasetService;
import com.github.pagehelper.PageInfo;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * DatasetController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 数据集")
@RestController
@RequestMapping("/dataset/")
@Validated
@Slf4j
public class DatasetController {

    @Resource
    private DatasetService datasetService;

    @PostMapping("/create")
    @Operation(summary = "创建数据集")
    //@PreAuthorize("@ss.hasPermission('dataset::create')")
    public CommonResult<Long> createDataset(@Valid @RequestBody DatasetSaveReqVO createReqVO) {
        return success(datasetService.createDataset(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新数据集")
    //@PreAuthorize("@ss.hasPermission('dataset::update')")
    public CommonResult<Boolean> updateDataset(@Valid @RequestBody DatasetSaveReqVO updateReqVO) {
        datasetService.updateDataset(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除数据集")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset::delete')")
    public CommonResult<Boolean> deleteDataset(@RequestParam("id") Long id) {
        datasetService.deleteDataset(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得数据集")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset::query')")
    public CommonResult<DatasetRespVO> getDataset(@RequestParam("id") Long id) {
        DatasetDO dataset = datasetService.getDataset(id);
        return success(BeanUtils.toBean(dataset, DatasetRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得数据集分页")
    //@PreAuthorize("@ss.hasPermission('dataset::query')")
    public PageInfo<DatasetDO> getDatasetPage(@Valid DatasetPageReqVO pageReqVO) {
        return datasetService.getDatasetPage(pageReqVO);
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出数据集 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset::export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetExcel(@Valid DatasetPageReqVO pageReqVO,
                                   HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetDO> list = datasetService.getDatasetPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "数据集.xls", "数据", DatasetRespVO.class,
                BeanUtils.toBean(list, DatasetRespVO.class));
    }

    @PostMapping("/upload-cover")
    @ApiOperation("上传数据集封面(minio)")
    R<String> uploadCover(@RequestPart("file") MultipartFile file) {
        try {
            return R.ok(datasetService.uploadCover(file), "上传数据集封面成功");
        } catch (Exception e) {
            log.error("Failed to upload cover,fileName:{} \n",
                    file.getOriginalFilename(), e);
            return R.fail("上传数据集封面失败");
        }
    }

    @PostMapping("/{datasetId}/set-auto-label-model")
    @Operation(summary = "设置自动化标注模型服务")
    public CommonResult<Boolean> setAutoLabelModel(
            @PathVariable("datasetId") Long datasetId,
            @Valid @RequestBody AutoLabelModelReqVO reqVO) {
        datasetService.setAutoLabelModel(datasetId, reqVO);
        return success(true);
    }

    @PostMapping("/{datasetId}/auto-label")
    @Operation(summary = "一键自动化标注")
    public CommonResult<Boolean> autoLabelDataset(
            @PathVariable("datasetId") Long datasetId) {
        datasetService.autoLabelDataset(datasetId);
        return success(true);
    }

    @PostMapping("/{datasetId}/split")
    @Operation(summary = "按比例划分数据集用途")
    public CommonResult<Boolean> splitDataset(
            @PathVariable("datasetId") Long datasetId,
            @Valid @RequestBody DatasetSplitReqVO reqVO) {
        datasetService.splitDataset(datasetId, reqVO);
        return success(true);
    }

    @PostMapping("/{datasetId}/reset")
    @Operation(summary = "一键重置数据集用途")
    public CommonResult<Boolean> resetDataset(
            @PathVariable("datasetId") Long datasetId) {
        datasetService.resetDataset(datasetId);
        return success(true);
    }
}