package com.basiclab.iot.dataset.controller;



import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.cache.StreamUrlCache;
import com.basiclab.iot.dataset.dal.dataobject.DatasetFrameTaskDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetFrameTaskService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;


/**
 * DatasetFrameTaskController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;


@Tag(name = "管理后台 - 视频流帧捕获任务")
@RestController
@RequestMapping("/dataset/frame-task")
@Validated
public class DatasetFrameTaskController {

    @Resource
    private DatasetFrameTaskService frameTaskService;

    @Autowired
    private StreamUrlCache streamUrlCache;

    @PostMapping("/create")
    @Operation(summary = "创建视频流帧捕获任务")
    //@PreAuthorize("@ss.hasPermission('dataset:frame-task:create')")
    public CommonResult<Long> createDatasetFrameTask(@Valid @RequestBody DatasetFrameTaskSaveReqVO createReqVO) {
        Long ret = frameTaskService.createDatasetFrameTask(createReqVO);
        streamUrlCache.manualRefresh();
        return success(ret);
    }

    @PutMapping("/update")
    @Operation(summary = "更新视频流帧捕获任务")
    //@PreAuthorize("@ss.hasPermission('dataset:frame-task:update')")
    public CommonResult<Boolean> updateDatasetFrameTask(@Valid @RequestBody DatasetFrameTaskSaveReqVO updateReqVO) {
        frameTaskService.updateDatasetFrameTask(updateReqVO);
        streamUrlCache.manualRefresh();
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除视频流帧捕获任务")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:frame-task:delete')")
    public CommonResult<Boolean> deleteDatasetFrameTask(@RequestParam("id") Long id) {
        frameTaskService.deleteDatasetFrameTask(id);
        streamUrlCache.manualRefresh();
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得视频流帧捕获任务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:frame-task:query')")
    public CommonResult<DatasetFrameTaskRespVO> getDatasetFrameTask(@RequestParam("id") Long id) {
        DatasetFrameTaskDO frameTask = frameTaskService.getDatasetFrameTask(id);
        return success(BeanUtils.toBean(frameTask, DatasetFrameTaskRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得视频流帧捕获任务分页")
    //@PreAuthorize("@ss.hasPermission('dataset:frame-task:query')")
    public CommonResult<PageResult<DatasetFrameTaskRespVO>> getDatasetFrameTaskPage(@Valid DatasetFrameTaskPageReqVO pageReqVO) {
        PageResult<DatasetFrameTaskDO> pageResult = frameTaskService.getDatasetFrameTaskPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetFrameTaskRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出视频流帧捕获任务 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:frame-task:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetFrameTaskExcel(@Valid DatasetFrameTaskPageReqVO pageReqVO,
                                            HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetFrameTaskDO> list = frameTaskService.getDatasetFrameTaskPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "视频流帧捕获任务.xls", "数据", DatasetFrameTaskRespVO.class,
                BeanUtils.toBean(list, DatasetFrameTaskRespVO.class));
    }

}