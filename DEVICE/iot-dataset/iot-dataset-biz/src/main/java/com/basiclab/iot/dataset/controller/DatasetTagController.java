package com.basiclab.iot.dataset.controller;



import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagRespVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTagService;
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
 * DatasetTagController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 数据集标签")
@RestController
@RequestMapping("/dataset/tag")
@Validated
public class DatasetTagController {

    @Resource
    private DatasetTagService datasetTagService;

    @PostMapping("/create")
    @Operation(summary = "创建数据集标签")
    //@PreAuthorize("@ss.hasPermission('dataset:tag:create')")
    public CommonResult<Long> createDatasetTag(@Valid @RequestBody DatasetTagSaveReqVO createReqVO) {
        return success(datasetTagService.createDatasetTag(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新数据集标签")
    //@PreAuthorize("@ss.hasPermission('dataset:tag:update')")
    public CommonResult<Boolean> updateDatasetTag(@Valid @RequestBody DatasetTagSaveReqVO updateReqVO) {
        datasetTagService.updateDatasetTag(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除数据集标签")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('dataset:tag:delete')")
    public CommonResult<Boolean> deleteDatasetTag(@RequestParam("id") Long id) {
        datasetTagService.deleteDatasetTag(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得数据集标签")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('dataset:tag:query')")
    public CommonResult<DatasetTagRespVO> getDatasetTag(@RequestParam("id") Long id) {
        DatasetTagDO tag = datasetTagService.getDatasetTag(id);
        return success(BeanUtils.toBean(tag, DatasetTagRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得数据集标签分页")
    //@PreAuthorize("@ss.hasPermission('dataset:tag:query')")
    public CommonResult<PageResult<DatasetTagRespVO>> getDatasetTagPage(@Valid DatasetTagPageReqVO pageReqVO) {
        PageResult<DatasetTagDO> pageResult = datasetTagService.getDatasetTagPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DatasetTagRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出数据集标签 Excel")
    //@PreAuthorize("@ss.hasPermission('dataset:tag:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDatasetTagExcel(@Valid DatasetTagPageReqVO pageReqVO,
                                      HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DatasetTagDO> list = datasetTagService.getDatasetTagPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "数据集标签.xls", "数据", DatasetTagRespVO.class,
                BeanUtils.toBean(list, DatasetTagRespVO.class));
    }

}