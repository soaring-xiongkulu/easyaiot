package com.basiclab.iot.infra.controller.admin.demo.demo02;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.infra.controller.admin.demo.demo02.vo.Demo02CategoryListReqVO;
import com.basiclab.iot.infra.controller.admin.demo.demo02.vo.Demo02CategoryRespVO;
import com.basiclab.iot.infra.controller.admin.demo.demo02.vo.Demo02CategorySaveReqVO;
import com.basiclab.iot.infra.dal.dataobject.demo.demo02.Demo02CategoryDO;
import com.basiclab.iot.infra.service.demo.demo02.Demo02CategoryService;
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
 * Demo02CategoryController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 示例分类")
@RestController
@RequestMapping("/infra/demo02-category")
@Validated
public class Demo02CategoryController {

    @Resource
    private Demo02CategoryService demo02CategoryService;

    @PostMapping("/create")
    @Operation(summary = "创建示例分类")
    //@PreAuthorize("@ss.hasPermission('infra:demo02-category:create')")
    public CommonResult<Long> createDemo02Category(@Valid @RequestBody Demo02CategorySaveReqVO createReqVO) {
        return success(demo02CategoryService.createDemo02Category(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新示例分类")
    //@PreAuthorize("@ss.hasPermission('infra:demo02-category:update')")
    public CommonResult<Boolean> updateDemo02Category(@Valid @RequestBody Demo02CategorySaveReqVO updateReqVO) {
        demo02CategoryService.updateDemo02Category(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除示例分类")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('infra:demo02-category:delete')")
    public CommonResult<Boolean> deleteDemo02Category(@RequestParam("id") Long id) {
        demo02CategoryService.deleteDemo02Category(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得示例分类")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('infra:demo02-category:query')")
    public CommonResult<Demo02CategoryRespVO> getDemo02Category(@RequestParam("id") Long id) {
        Demo02CategoryDO demo02Category = demo02CategoryService.getDemo02Category(id);
        return success(BeanUtils.toBean(demo02Category, Demo02CategoryRespVO.class));
    }

    @GetMapping("/list")
    @Operation(summary = "获得示例分类列表")
    //@PreAuthorize("@ss.hasPermission('infra:demo02-category:query')")
    public CommonResult<List<Demo02CategoryRespVO>> getDemo02CategoryList(@Valid Demo02CategoryListReqVO listReqVO) {
        List<Demo02CategoryDO> list = demo02CategoryService.getDemo02CategoryList(listReqVO);
        return success(BeanUtils.toBean(list, Demo02CategoryRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出示例分类 Excel")
    //@PreAuthorize("@ss.hasPermission('infra:demo02-category:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportDemo02CategoryExcel(@Valid Demo02CategoryListReqVO listReqVO,
                                          HttpServletResponse response) throws IOException {
        List<Demo02CategoryDO> list = demo02CategoryService.getDemo02CategoryList(listReqVO);
        // 导出 Excel
        ExcelUtils.write(response, "示例分类.xls", "数据", Demo02CategoryRespVO.class,
                BeanUtils.toBean(list, Demo02CategoryRespVO.class));
    }

}