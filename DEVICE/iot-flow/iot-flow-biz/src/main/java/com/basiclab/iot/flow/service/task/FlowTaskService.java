package com.basiclab.iot.flow.service.task;

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

import java.util.List;

/**
 * 流程任务 Service 接口
 */
public interface FlowTaskService {

    PageResult<TaskVO> getTaskTodoPage(Long userId, PageParam pageParam, String name, String processInstanceName);

    PageResult<TaskVO> getTaskDonePage(Long userId, PageParam pageParam, String name, String processInstanceName);

    PageResult<TaskVO> getTaskManagerPage(PageParam pageParam, String name, String processInstanceName);

    /** 待办任务数量（APP/PC 角标） */
    Long getTaskTodoCount(Long userId);

    void approveTask(Long userId, ApproveReq reqVO);

    void rejectTask(Long userId, RejectReq reqVO);

    void returnTask(Long userId, ReturnReq reqVO);

    void delegateTask(Long userId, AssignReq reqVO);

    void transferTask(Long userId, AssignReq reqVO);

    void copyTask(Long userId, CopyReq reqVO);

    void createSignTask(Long userId, CreateSignReq reqVO);

    void deleteSignTask(Long userId, ReasonReq reqVO);

    /** 撤回自己已审批的任务（下一节点未处理前） */
    void withdrawTask(Long userId, ReasonReq reqVO);

    /** 实例的全部任务（审批时间线/列表） */
    List<TaskVO> getTaskListByProcessInstanceId(String processInstanceId);

    /** 可退回的节点列表 */
    List<TaskVO> getTaskListByReturn(Long userId, String taskId);

}
