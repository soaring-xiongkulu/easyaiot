package com.basiclab.iot.dataset.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskUserDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTaskUserService;
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
 * DatasetTaskUserController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 标注任务用户")
@RestController
@RequestMapping("/dataset/task-user")
@Validated
public class DatasetTaskUserController {

    @Resource
    private DatasetTaskUserService datasetTaskUserService;

    @PostMapping("/create")
    @Operation(summary = "创建标注任务用户")
    //@PreAuthorize("@ss.hasPermission('dataset:task-user:create')")
    public CommonResult<Long> createDatasetTaskUser(@Valid @RequestBody DatasetTaskUserSaveReqVO createReqVO) {
        return success(datasetTaskUserService.createDatasetTaskUser(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新标注任务用户")
    //@PreAuthorize("@ss.hasPermission('dataset:task-user:update')")
    public CommonResult<Boolean> updateDatasetTaskUser(@Valid @RequestBody DatasetTaskUserSaveReqVO updateReqVO) {
        datasetTaskUserService.updateDatasetTaskUser(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除标注任务用户")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:task-user:delete')")
    public CommonResult<Boolean> deleteDatasetTaskUser(@RequestParam("id") Long id) {
        datasetTaskUserService.deleteDatasetTaskUser(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得标注任务用户")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:task-user:query')")
    public CommonResult<DatasetTaskUserRespVO> getDatasetTaskUser(@RequestParam("id") Long id) {
        DatasetTaskUserDO taskUser = datasetTaskUserService.getDatasetTaskUser(id);
        return success(BeanUtils.toBean(taskUser, DatasetTaskUserRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得标注任务用户分页")
    //@PreAuthorize("@ss.hasPermission('dataset:task-user:query')")
    public CommonResult<PageResult<DatasetTaskUserRespVO>> getDatasetTaskUserPage(@Valid DatasetTaskUserPageReqVO pageReqVO) {
        PageResult<DatasetTaskUserDO> pageResult = datasetTaskUserService.getDatasetTaskUserPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetTaskUserRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出标注任务用户 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:task-user:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetTaskUserExcel(@Valid DatasetTaskUserPageReqVO pageReqVO,
                                           HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetTaskUserDO> list = datasetTaskUserService.getDatasetTaskUserPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "标注任务用户.xls", "数据", DatasetTaskUserRespVO.class,
                BeanUtils.toBean(list, DatasetTaskUserRespVO.class));
    }

}