package com.basiclab.iot.flow.controller.admin.task;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.ApproveReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.AssignReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.CopyReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.CreateSignReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.ReasonReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.RejectReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.ReturnReq;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs.TaskVO;
import com.basiclab.iot.flow.service.task.FlowTaskService;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - FLOW 流程任务")
@RestController
@RequestMapping("/flow/task")
@Validated
public class FlowTaskController {

    @Resource
    private FlowTaskService taskService;

    @GetMapping("/todo-page")
    @Operation(summary = "待办任务分页")
    public CommonResult<PageResult<TaskVO>> getTaskTodoPage(@Validated PageParam pageParam,
                                                          @RequestParam(value = "name", required = false) String name,
                                                          @RequestParam(value = "processInstanceName", required = false) String processInstanceName) {
        return success(taskService.getTaskTodoPage(SecurityFrameworkUtils.getLoginUserId(),
                pageParam, name, processInstanceName));
    }

    @GetMapping("/done-page")
    @Operation(summary = "已办任务分页")
    public CommonResult<PageResult<TaskVO>> getTaskDonePage(@Validated PageParam pageParam,
                                                          @RequestParam(value = "name", required = false) String name,
                                                          @RequestParam(value = "processInstanceName", required = false) String processInstanceName) {
        return success(taskService.getTaskDonePage(SecurityFrameworkUtils.getLoginUserId(),
                pageParam, name, processInstanceName));
    }

    @GetMapping("/manager-page")
    @Operation(summary = "管理员任务分页")
    public CommonResult<PageResult<TaskVO>> getTaskManagerPage(@Validated PageParam pageParam,
                                                             @RequestParam(value = "name", required = false) String name,
                                                             @RequestParam(value = "processInstanceName", required = false) String processInstanceName) {
        return success(taskService.getTaskManagerPage(pageParam, name, processInstanceName));
    }

    @GetMapping("/todo-count")
    @Operation(summary = "待办任务数量（角标）")
    public CommonResult<Long> getTaskTodoCount() {
        return success(taskService.getTaskTodoCount(SecurityFrameworkUtils.getLoginUserId()));
    }

    @PutMapping("/approve")
    @Operation(summary = "通过审批")
    public CommonResult<Boolean> approveTask(@RequestBody ApproveReq reqVO) {
        taskService.approveTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/reject")
    @Operation(summary = "拒绝审批")
    public CommonResult<Boolean> rejectTask(@RequestBody RejectReq reqVO) {
        taskService.rejectTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/return")
    @Operation(summary = "退回到指定节点")
    public CommonResult<Boolean> returnTask(@RequestBody ReturnReq reqVO) {
        taskService.returnTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/delegate")
    @Operation(summary = "委派任务")
    public CommonResult<Boolean> delegateTask(@RequestBody AssignReq reqVO) {
        taskService.delegateTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/transfer")
    @Operation(summary = "转办任务")
    public CommonResult<Boolean> transferTask(@RequestBody AssignReq reqVO) {
        taskService.transferTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/copy")
    @Operation(summary = "抄送任务")
    public CommonResult<Boolean> copyTask(@RequestBody CopyReq reqVO) {
        taskService.copyTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/create-sign")
    @Operation(summary = "加签")
    public CommonResult<Boolean> createSignTask(@RequestBody CreateSignReq reqVO) {
        taskService.createSignTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/delete-sign")
    @Operation(summary = "减签")
    public CommonResult<Boolean> deleteSignTask(@RequestBody ReasonReq reqVO) {
        taskService.deleteSignTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @PutMapping("/withdraw")
    @Operation(summary = "撤回已审批任务")
    public CommonResult<Boolean> withdrawTask(@RequestBody ReasonReq reqVO) {
        taskService.withdrawTask(SecurityFrameworkUtils.getLoginUserId(), reqVO);
        return success(true);
    }

    @GetMapping("/list-by-process-instance-id")
    @Operation(summary = "查询流程实例的任务列表")
    @Parameter(name = "processInstanceId", description = "流程实例编号", required = true)
    public CommonResult<List<TaskVO>> getTaskListByProcessInstanceId(@RequestParam("processInstanceId") String processInstanceId) {
        return success(taskService.getTaskListByProcessInstanceId(processInstanceId));
    }

    @GetMapping("/list-by-return")
    @Operation(summary = "查询可退回的节点列表")
    @Parameter(name = "id", description = "任务编号", required = true)
    public CommonResult<List<TaskVO>> getTaskListByReturn(@RequestParam("id") String id) {
        return success(taskService.getTaskListByReturn(SecurityFrameworkUtils.getLoginUserId(), id));
    }

}
