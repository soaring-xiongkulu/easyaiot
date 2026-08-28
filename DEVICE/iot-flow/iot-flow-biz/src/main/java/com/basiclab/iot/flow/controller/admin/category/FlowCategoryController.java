package com.basiclab.iot.flow.controller.admin.category;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.category.vo.FlowCategoryVO;
import com.basiclab.iot.flow.dal.dataobject.FlowCategoryDO;
import com.basiclab.iot.flow.service.category.FlowCategoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 流程分类")
@RestController
@RequestMapping("/flow/category")
@Validated
public class FlowCategoryController {

    @Resource
    private FlowCategoryService categoryService;

    @PostMapping("/create")
    @Operation(summary = "创建流程分类")
    public CommonResult<Long> createCategory(@Valid @RequestBody FlowCategoryVO reqVO) {
        return success(categoryService.createCategory(reqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新流程分类")
    public CommonResult<Boolean> updateCategory(@Valid @RequestBody FlowCategoryVO reqVO) {
        categoryService.updateCategory(reqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除流程分类")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Boolean> deleteCategory(@RequestParam("id") Long id) {
        categoryService.deleteCategory(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得流程分类")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<FlowCategoryVO> getCategory(@RequestParam("id") Long id) {
        return success(FlowCategoryVO.of(categoryService.getCategory(id)));
    }

    @GetMapping("/page")
    @Operation(summary = "获得流程分类分页")
    public CommonResult<PageResult<FlowCategoryVO>> getCategoryPage(@Validated PageParam pageParam,
                                                                    @RequestParam(value = "name", required = false) String name,
                                                                    @RequestParam(value = "code", required = false) String code,
                                                                    @RequestParam(value = "status", required = false) Integer status) {
        PageResult<FlowCategoryDO> page = categoryService.getCategoryPage(pageParam, name, code, status);
        return success(new PageResult<>(page.getList().stream().map(FlowCategoryVO::of).toList(), page.getTotal()));
    }

    @GetMapping("/simple-list")
    @Operation(summary = "获得流程分类精简列表")
    public CommonResult<List<FlowCategoryVO>> getCategorySimpleList() {
        return success(categoryService.getCategorySimpleList().stream().map(FlowCategoryVO::of).toList());
    }

}
