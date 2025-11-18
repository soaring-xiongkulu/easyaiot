package com.basiclab.iot.dataset.controller;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetImageService;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.*;

/**
 * DatasetImageController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 图片数据集")
@RestController
@RequestMapping("/dataset/image")
@Validated
public class DatasetImageController {

    @Resource
    private DatasetImageService datasetImageService;

    @PostMapping("/create")
    @Operation(summary = "创建图片数据集")
    //@PreAuthorize("@ss.hasPermission('dataset:image:create')")
    public CommonResult<Long> createDatasetImage(@Valid @RequestBody DatasetImageSaveReqVO createReqVO) {
        return success(datasetImageService.createDatasetImage(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新图片数据集")
    //@PreAuthorize("@ss.hasPermission('dataset:image:update')")
    public CommonResult<Boolean> updateDatasetImage(@Valid @RequestBody DatasetImageSaveReqVO updateReqVO) {
        datasetImageService.updateDatasetImage(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete/{id}")
    @Operation(summary = "删除图片数据集")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:image:delete')")
    public CommonResult<Boolean> deleteDatasetImage(@PathVariable("id") Long id) {
        datasetImageService.deleteDatasetImage(id);
        return success(true);
    }

    @DeleteMapping("/batchDelete/{ids}")
    @Operation(summary = "批量删除图片数据集")
    @Parameter(name = "ids", description = "ID列表", required = true)
    public CommonResult<Boolean> deleteDatasetImages(@PathVariable("ids") List<Long> ids) {
        datasetImageService.deleteDatasetImages(ids);
        return success(true);
    }


    @GetMapping("/get")
    @Operation(summary = "获得图片数据集")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:image:query')")
    public CommonResult<DatasetImageRespVO> getDatasetImage(@RequestParam("id") Long id) {
        DatasetImageDO image = datasetImageService.getDatasetImage(id);
        return success(BeanUtils.toBean(image, DatasetImageRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得图片数据集分页")
    //@PreAuthorize("@ss.hasPermission('dataset:image:query')")
    public CommonResult<PageResult<DatasetImageRespVO>> getDatasetImagePage(@Valid DatasetImagePageReqVO pageReqVO) {
        PageResult<DatasetImageDO> pageResult = datasetImageService.getDatasetImagePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetImageRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出图片数据集 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:image:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetImageExcel(@Valid DatasetImagePageReqVO pageReqVO,
                                        HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetImageDO> list = datasetImageService.getDatasetImagePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "图片数据集.xls", "数据", DatasetImageRespVO.class,
                BeanUtils.toBean(list, DatasetImageRespVO.class));
    }

    @PostMapping("/upload")
    @Operation(summary = "上传图片或压缩包")
    public CommonResult<Boolean> uploadDatasetImage(
            @Parameter(description = "上传的文件", required = true)
            @RequestParam("file") MultipartFile file,
            @Parameter(description = "数据集ID", required = true)
            @RequestParam("datasetId") Long datasetId,
            @Parameter(description = "是否为压缩包", required = true)
            @RequestParam("isZip") Boolean isZip) {

        // 验证文件类型
        if (file.isEmpty()) {
            throw exception(FILE_UPLOAD_FAILED, "上传文件不能为空");
        }

        if (isZip && !"application/zip".equals(file.getContentType())) {
            throw exception(INVALID_FILE_TYPE, "仅支持ZIP格式");
        } else if (!isZip && !file.getContentType().startsWith("image/")) {
            throw exception(INVALID_FILE_TYPE, "仅支持图片格式");
        }

        // 验证文件大小
        long maxSize = isZip ? 200 * 1024 * 1024 : 50 * 1024 * 1024;
        if (file.getSize() > maxSize) {
            String msg = isZip ? "压缩包不能超过200MB" : "图片不能超过50MB";
            throw exception(FILE_SIZE_EXCEEDED, msg);
        }

        // 调用服务层处理上传
        datasetImageService.processUpload(file, datasetId, isZip);
        return CommonResult.success(true);
    }

    @PostMapping("/upload-file")
    @ApiOperation("上传数据集文件")
    R<String> uploadFile(@RequestPart("file") MultipartFile file) {
        try {
            return R.ok(datasetImageService.uploadFile(file), "上传数据集文件成功");
        } catch (Exception e) {
            return R.fail("上传数据集文件失败");
        }
    }

    @GetMapping("/{datasetId}/check-sync-condition")
    @Operation(summary = "检查数据集同步条件")
    public CommonResult<Boolean> checkSyncCondition(
            @PathVariable("datasetId") Long datasetId) {
        return success(datasetImageService.checkSyncCondition(datasetId));
    }

    @PostMapping("/{datasetId}/sync-to-minio")
    @Operation(summary = "同步数据集到Minio")
    public CommonResult<Boolean> syncToMinio(
            @PathVariable("datasetId") Long datasetId) {
        datasetImageService.syncToMinio(datasetId);
        return success(true);
    }
}