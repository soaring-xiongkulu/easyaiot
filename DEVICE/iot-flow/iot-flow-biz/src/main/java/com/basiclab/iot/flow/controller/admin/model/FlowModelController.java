package com.basiclab.iot.flow.controller.admin.model;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.service.model.FlowModelService;
import com.basiclab.iot.flow.service.model.FlowModelService.FlowModelDetail;
import com.basiclab.iot.flow.service.model.FlowModelService.FlowModelPageItem;
import com.basiclab.iot.flow.service.model.FlowModelService.FlowModelSaveParams;
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
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 流程模型")
@RestController
@RequestMapping("/flow/model")
@Validated
public class FlowModelController {

    @Resource
    private FlowModelService modelService;

    @GetMapping("/page")
    @Operation(summary = "获得流程模型分页")
    public CommonResult<PageResult<FlowModelPageItem>> getModelPage(@Validated PageParam pageParam,
                                                                    @RequestParam(value = "key", required = false) String key,
                                                                    @RequestParam(value = "name", required = false) String name,
                                                                    @RequestParam(value = "category", required = false) String category) {
        return success(modelService.getModelPage(pageParam, key, name, category));
    }

    @GetMapping("/get")
    @Operation(summary = "获得流程模型详情")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<FlowModelDetail> getModel(@RequestParam("id") String id) {
        return success(modelService.getModel(id));
    }

    @PostMapping("/create")
    @Operation(summary = "新建流程模型")
    public CommonResult<String> createModel(@RequestBody FlowModelSaveParams params) {
        return success(modelService.createModel(params));
    }

    @PutMapping("/update")
    @Operation(summary = "修改流程模型基本信息")
    public CommonResult<Boolean> updateModel(@RequestBody FlowModelSaveParams params) {
        modelService.updateModel(params);
        return success(true);
    }

    @PutMapping("/simple/update")
    @Operation(summary = "修改流程模型 Simple 设计器 JSON")
    public CommonResult<Boolean> updateModelSimple(@RequestBody Map<String, Object> body) {
        modelService.updateModelSimple(String.valueOf(body.get("id")), body.get("simpleModel"));
        return success(true);
    }

    @GetMapping("/simple/get")
    @Operation(summary = "读取流程模型 Simple 设计器 JSON")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Object> getModelSimple(@RequestParam("id") String id) {
        return success(modelService.getModelSimple(id));
    }

    @PostMapping("/deploy")
    @Operation(summary = "部署流程模型")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<String> deployModel(@RequestParam("id") String id) {
        return success(modelService.deployModel(id));
    }

    @PutMapping("/update-state")
    @Operation(summary = "修改模型状态（1 激活 / 2 挂起）")
    public CommonResult<Boolean> updateModelState(@RequestBody Map<String, Object> body) {
        modelService.updateModelState(String.valueOf(body.get("id")), Integer.valueOf(String.valueOf(body.get("state"))));
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除流程模型")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<Boolean> deleteModel(@RequestParam("id") String id) {
        modelService.deleteModel(id);
        return success(true);
    }

    @PostMapping("/copy")
    @Operation(summary = "复制流程模型")
    @Parameter(name = "id", description = "编号", required = true)
    public CommonResult<String> copyModel(@RequestParam("id") String id) {
        return success(modelService.copyModel(id));
    }

}
