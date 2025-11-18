package com.basiclab.iot.dataset.controller;


import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTaskService;
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
 * DatasetTaskController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 标注任务")
@RestController
@RequestMapping("/dataset/task")
@Validated
public class DatasetTaskController {

    @Resource
    private DatasetTaskService datasetTaskService;

    @PostMapping("/create")
    @Operation(summary = "创建标注任务")
    //@PreAuthorize("@ss.hasPermission('dataset:task:create')")
    public CommonResult<Long> createDatasetTask(@Valid @RequestBody DatasetTaskSaveReqVO createReqVO) {
        return success(datasetTaskService.createDatasetTask(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新标注任务")
    //@PreAuthorize("@ss.hasPermission('dataset:task:update')")
    public CommonResult<Boolean> updateDatasetTask(@Valid @RequestBody DatasetTaskSaveReqVO updateReqVO) {
        datasetTaskService.updateDatasetTask(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除标注任务")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:task:delete')")
    public CommonResult<Boolean> deleteDatasetTask(@RequestParam("id") Long id) {
        datasetTaskService.deleteDatasetTask(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得标注任务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:task:query')")
    public CommonResult<DatasetTaskRespVO> getDatasetTask(@RequestParam("id") Long id) {
        DatasetTaskDO task = datasetTaskService.getDatasetTask(id);
        return success(BeanUtils.toBean(task, DatasetTaskRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得标注任务分页")
    //@PreAuthorize("@ss.hasPermission('dataset:task:query')")
    public CommonResult<PageResult<DatasetTaskRespVO>> getDatasetTaskPage(@Valid DatasetTaskPageReqVO pageReqVO) {
        PageResult<DatasetTaskDO> pageResult = datasetTaskService.getDatasetTaskPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetTaskRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出标注任务 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:task:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetTaskExcel(@Valid DatasetTaskPageReqVO pageReqVO,
                                       HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetTaskDO> list = datasetTaskService.getDatasetTaskPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "标注任务.xls", "数据", DatasetTaskRespVO.class,
                BeanUtils.toBean(list, DatasetTaskRespVO.class));
    }

}