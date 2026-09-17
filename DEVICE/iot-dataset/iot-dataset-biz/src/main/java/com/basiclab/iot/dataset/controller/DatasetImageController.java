package com.basiclab.iot.dataset.controller;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetChunkUploadInitReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetChunkUploadInitRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetChunkUploadStatusRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageImportTaskRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImagePageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageSaveReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetImageUploadRespVO;
import com.basiclab.iot.dataset.service.DatasetChunkUploadService;
import com.basiclab.iot.dataset.service.DatasetImageImportTaskService;
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

    @Resource
    private DatasetChunkUploadService datasetChunkUploadService;

    @Resource
    private DatasetImageImportTaskService datasetImageImportTaskService;

    /** 直传上限：小文件可走 /upload，大文件请使用分片上传 */
    private static final long DIRECT_UPLOAD_IMAGE_MAX = 50L * 1024 * 1024;
    private static final long DIRECT_UPLOAD_ZIP_MAX = 200L * 1024 * 1024;

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

    @PutMapping("/batchClearAnnotations/{ids}")
    @Operation(summary = "批量清除图片标注并恢复为待标注")
    @Parameter(name = "ids", description = "图片ID列表", required = true)
    public CommonResult<Boolean> clearDatasetImageAnnotations(@PathVariable("ids") List<Long> ids) {
        datasetImageService.clearDatasetImageAnnotations(ids);
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
    public CommonResult<DatasetImageUploadRespVO> uploadDatasetImage(
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

        if (Boolean.TRUE.equals(isZip)) {
            if (!isZipFile(file)) {
                throw exception(INVALID_FILE_TYPE, "仅支持ZIP格式");
            }
        } else {
            String contentType = file.getContentType();
            if (contentType == null || !contentType.startsWith("image/")) {
                throw exception(INVALID_FILE_TYPE, "仅支持图片格式");
            }
        }

        // 直传仅用于小文件；大文件请使用分片上传（最大 200GB）
        long maxSize = Boolean.TRUE.equals(isZip) ? DIRECT_UPLOAD_ZIP_MAX : DIRECT_UPLOAD_IMAGE_MAX;
        if (file.getSize() > maxSize) {
            String msg = Boolean.TRUE.equals(isZip)
                    ? "压缩包超过 200MB 请使用分片上传"
                    : "图片超过 50MB 请使用分片上传";
            throw exception(FILE_SIZE_EXCEEDED, msg);
        }

        DatasetImageUploadRespVO uploadResult = datasetImageService.processUpload(file, datasetId, isZip);
        if ("processing".equals(uploadResult.getImportStatus())) {
            return success(uploadResult);
        }
        if (uploadResult.getSuccessCount() <= 0) {
            String detail = uploadResult.getFailedCount() > 0
                    ? "压缩包内图片均上传失败，请检查文件或存储配置"
                    : "压缩包中未找到有效的 JPG/PNG 图片";
            throw exception(FILE_UPLOAD_FAILED, detail);
        }

        CommonResult<DatasetImageUploadRespVO> response = CommonResult.success(uploadResult);
        if (uploadResult.getFailedCount() > 0) {
            response.setMsg(String.format("成功上传 %d 个文件，%d 个失败",
                    uploadResult.getSuccessCount(), uploadResult.getFailedCount()));
        }
        return response;
    }

    private static boolean isZipFile(MultipartFile file) {
        String filename = file.getOriginalFilename();
        if (filename != null && filename.toLowerCase().endsWith(".zip")) {
            return true;
        }
        String contentType = file.getContentType();
        if (contentType == null) {
            return false;
        }
        String normalized = contentType.toLowerCase();
        return "application/zip".equals(normalized)
                || "application/x-zip-compressed".equals(normalized)
                || "application/octet-stream".equals(normalized)
                || "multipart/x-zip".equals(normalized);
    }

    @PostMapping("/upload/chunk/init")
    @Operation(summary = "初始化分片上传（支持断点续传）")
    public CommonResult<DatasetChunkUploadInitRespVO> initChunkUpload(
            @Valid @RequestBody DatasetChunkUploadInitReqVO reqVO) {
        return success(datasetChunkUploadService.initUpload(reqVO));
    }

    @PostMapping("/upload/chunk")
    @Operation(summary = "上传单个分片")
    public CommonResult<Boolean> uploadChunk(
            @Parameter(description = "上传会话 ID", required = true) @RequestParam("uploadId") String uploadId,
            @Parameter(description = "分片序号（从 0 开始）", required = true) @RequestParam("chunkIndex") Integer chunkIndex,
            @Parameter(description = "分片数据", required = true) @RequestParam("chunk") MultipartFile chunk) {
        datasetChunkUploadService.uploadChunk(uploadId, chunkIndex, chunk);
        return success(true);
    }

    @GetMapping("/upload/chunk/status")
    @Operation(summary = "查询分片上传进度")
    public CommonResult<DatasetChunkUploadStatusRespVO> getChunkUploadStatus(
            @Parameter(description = "上传会话 ID", required = true) @RequestParam("uploadId") String uploadId) {
        return success(datasetChunkUploadService.getUploadStatus(uploadId));
    }

    @PostMapping("/upload/chunk/complete")
    @Operation(summary = "完成分片上传并入库")
    public CommonResult<DatasetImageUploadRespVO> completeChunkUpload(
            @Parameter(description = "上传会话 ID", required = true) @RequestParam("uploadId") String uploadId) {
        DatasetImageUploadRespVO uploadResult = datasetChunkUploadService.completeUpload(uploadId);
        if ("processing".equals(uploadResult.getImportStatus())) {
            return success(uploadResult);
        }
        if (uploadResult.getSuccessCount() <= 0) {
            String detail = uploadResult.getFailedCount() > 0
                    ? "压缩包内图片均上传失败，请检查文件或存储配置"
                    : "压缩包中未找到有效的 JPG/PNG 图片";
            throw exception(FILE_UPLOAD_FAILED, detail);
        }
        CommonResult<DatasetImageUploadRespVO> response = CommonResult.success(uploadResult);
        if (uploadResult.getFailedCount() > 0) {
            response.setMsg(String.format("成功上传 %d 个文件，%d 个失败",
                    uploadResult.getSuccessCount(), uploadResult.getFailedCount()));
        }
        return response;
    }

    @GetMapping("/import-task/{taskId}")
    @Operation(summary = "查询异步图片导入任务状态")
    public CommonResult<DatasetImageImportTaskRespVO> getImportTask(
            @Parameter(description = "导入任务 ID", required = true) @PathVariable("taskId") String taskId) {
        return success(datasetImageImportTaskService.getTask(taskId));
    }

    @DeleteMapping("/import-task/{taskId}")
    @Operation(summary = "取消异步导入任务")
    public CommonResult<Boolean> cancelImportTask(
            @Parameter(description = "导入任务 ID", required = true) @PathVariable("taskId") String taskId) {
        datasetImageImportTaskService.cancelTask(taskId);
        return success(true);
    }

    @DeleteMapping("/upload/chunk")
    @Operation(summary = "取消分片上传")
    public CommonResult<Boolean> abortChunkUpload(
            @Parameter(description = "上传会话 ID", required = true) @RequestParam("uploadId") String uploadId) {
        datasetChunkUploadService.abortUpload(uploadId);
        return success(true);
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
    public CommonResult<com.basiclab.iot.dataset.domain.dataset.vo.DatasetSyncCheckRespVO> checkSyncCondition(
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
