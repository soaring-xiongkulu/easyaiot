package com.basiclab.iot.dataset.controller;



import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskResultDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTaskResultService;
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

/**
 * DatasetTaskResultController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 标注任务结果")
@RestController
@RequestMapping("/dataset/task-result")
@Validated
public class DatasetTaskResultController {

    @Resource
    private DatasetTaskResultService datasetTaskResultService;

    @PostMapping("/create")
    @Operation(summary = "创建标注任务结果")
    //@PreAuthorize("@ss.hasPermission('dataset:task-result:create')")
    public CommonResult<Long> createDatasetTaskResult(@Valid @RequestBody DatasetTaskResultSaveReqVO createReqVO) {
        return success(datasetTaskResultService.createDatasetTaskResult(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新标注任务结果")
    //@PreAuthorize("@ss.hasPermission('dataset:task-result:update')")
    public CommonResult<Boolean> updateDatasetTaskResult(@Valid @RequestBody DatasetTaskResultSaveReqVO updateReqVO) {
        datasetTaskResultService.updateDatasetTaskResult(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除标注任务结果")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:task-result:delete')")
    public CommonResult<Boolean> deleteDatasetTaskResult(@RequestParam("id") Long id) {
        datasetTaskResultService.deleteDatasetTaskResult(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得标注任务结果")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:task-result:query')")
    public CommonResult<DatasetTaskResultRespVO> getDatasetTaskResult(@RequestParam("id") Long id) {
        DatasetTaskResultDO taskResult = datasetTaskResultService.getDatasetTaskResult(id);
        return success(BeanUtils.toBean(taskResult, DatasetTaskResultRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得标注任务结果分页")
    //@PreAuthorize("@ss.hasPermission('dataset:task-result:query')")
    public CommonResult<PageResult<DatasetTaskResultRespVO>> getDatasetTaskResultPage(@Valid DatasetTaskResultPageReqVO pageReqVO) {
        PageResult<DatasetTaskResultDO> pageResult = datasetTaskResultService.getDatasetTaskResultPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetTaskResultRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出标注任务结果 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:task-result:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetTaskResultExcel(@Valid DatasetTaskResultPageReqVO pageReqVO,
                                             HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetTaskResultDO> list = datasetTaskResultService.getDatasetTaskResultPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "标注任务结果.xls", "数据", DatasetTaskResultRespVO.class,
                BeanUtils.toBean(list, DatasetTaskResultRespVO.class));
    }

}