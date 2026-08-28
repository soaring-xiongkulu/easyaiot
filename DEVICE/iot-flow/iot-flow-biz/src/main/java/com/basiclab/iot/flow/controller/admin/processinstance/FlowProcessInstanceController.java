package com.basiclab.iot.flow.controller.admin.processinstance;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.ApprovalDetail;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.BpmnModelView;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.CancelReq;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.CreateReq;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.Instance;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.NextApprovalNode;
import com.basiclab.iot.flow.dal.dataobject.FlowProcessInstanceCopyDO;
import com.basiclab.iot.flow.service.instance.FlowProcessInstanceService;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 流程实例")
@RestController
@RequestMapping("/flow/process-instance")
@Validated
public class FlowProcessInstanceController {

    @Resource
    private FlowProcessInstanceService processInstanceService;

    @PostMapping("/create")
    @Operation(summary = "发起流程")
    public CommonResult<String> createProcessInstance(@Valid @RequestBody CreateReq reqVO) {
        return success(processInstanceService.createProcessInstance(
                SecurityFrameworkUtils.getLoginUserId(), reqVO));
    }

    @GetMapping("/my-page")
    @Operation(summary = "我发起的流程实例分页")
    public CommonResult<PageResult<Instance>> getMyProcessInstancePage(@Validated PageParam pageParam,
                                                                       @RequestParam(value = "name", required = false) String name,
                                                                       @RequestParam(value = "processDefinitionKey", required = false) String processDefinitionKey,
                                                                       @RequestParam(value = "categoryId", required = false) String categoryId,
                                                                       @RequestParam(value = "status", required = false) Integer status) {
        return success(processInstanceService.getMyProcessInstancePage(
                SecurityFrameworkUtils.getLoginUserId(), pageParam, name, processDefinitionKey, categoryId, status));
    }

    @GetMapping("/manager-page")
    @Operation(summary = "管理员查询全部流程实例分页")
    public CommonResult<PageResult<Instance>> getManagerProcessInstancePage(@Validated PageParam pageParam,
                                                                            @RequestParam(value = "name", required = false) String name,
                                                                            @RequestParam(value = "processDefinitionKey", required = false) String processDefinitionKey,
                                                                            @RequestParam(value = "categoryId", required = false) String categoryId,
                                                                            @RequestParam(value = "status", required = false) Integer status) {
        return success(processInstanceService.getManagerProcessInstancePage(
                pageParam, name, processDefinitionKey, categoryId, status));
    }

    @GetMapping("/get")
    @Operation(summary = "查询流程实例详情")
    @Parameter(name = "id", description = "流程实例编号", required = true)
    public CommonResult<Instance> getProcessInstance(@RequestParam("id") String id) {
        return success(processInstanceService.getProcessInstance(id));
    }

    @GetMapping("/get-approval-detail")
    @Operation(summary = "审批详情聚合（实例 + 节点审批进度）")
    public CommonResult<ApprovalDetail> getApprovalDetail(@RequestParam("id") String id,
                                                          @RequestParam(value = "taskId", required = false) String taskId,
                                                          @RequestParam(value = "activityId", required = false) String activityId) {
        return success(processInstanceService.getApprovalDetail(id, taskId));
    }

    @GetMapping("/get-bpmn-model-view")
    @Operation(summary = "Simple 模型运行视图（含节点染色 ID 集合）")
    public CommonResult<BpmnModelView> getProcessInstanceBpmnModelView(@RequestParam("id") String id) {
        return success(processInstanceService.getBpmnModelView(id));
    }

    @GetMapping("/get-next-approval-nodes")
    @Operation(summary = "预测下一审批节点")
    public CommonResult<List<NextApprovalNode>> getNextApprovalNodes(
            @RequestParam("processDefinitionId") String processDefinitionId,
            @RequestParam(value = "activityId", required = false) String activityId,
            @RequestParam(value = "variables", required = false) Map<String, Object> variables) {
        return success(processInstanceService.getNextApprovalNodes(processDefinitionId, activityId, variables));
    }

    @DeleteMapping("/cancel-by-start-user")
    @Operation(summary = "发起人取消流程")
    public CommonResult<Boolean> cancelProcessInstanceByStartUser(@Valid @RequestBody CancelReq reqVO) {
        processInstanceService.cancelProcessInstanceByStartUser(
                SecurityFrameworkUtils.getLoginUserId(), reqVO.getId(), reqVO.getReason());
        return success(true);
    }

    @DeleteMapping("/cancel-by-admin")
    @Operation(summary = "管理员终止流程")
    public CommonResult<Boolean> cancelProcessInstanceByAdmin(@Valid @RequestBody CancelReq reqVO) {
        processInstanceService.cancelProcessInstanceByAdmin(
                SecurityFrameworkUtils.getLoginUserId(), reqVO.getId(), reqVO.getReason());
        return success(true);
    }

    @GetMapping("/copy/page")
    @Operation(summary = "抄送我的分页")
    public CommonResult<PageResult<FlowProcessInstanceCopyDO>> getProcessInstanceCopyPage(
            @Validated PageParam pageParam,
            @RequestParam(value = "processInstanceName", required = false) String processInstanceName) {
        return success(processInstanceService.getProcessInstanceCopyPage(
                SecurityFrameworkUtils.getLoginUserId(), pageParam, processInstanceName));
    }

}
