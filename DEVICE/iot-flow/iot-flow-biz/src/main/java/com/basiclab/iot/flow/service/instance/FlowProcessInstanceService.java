package com.basiclab.iot.flow.service.instance;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.ApprovalDetail;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.BpmnModelView;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.CreateReq;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.Instance;
import com.basiclab.iot.flow.controller.admin.processinstance.FlowProcessInstanceVOs.NextApprovalNode;
import com.basiclab.iot.flow.dal.dataobject.FlowProcessInstanceCopyDO;

import java.util.List;
import java.util.Map;

/**
 * 流程实例 Service 接口
 */
public interface FlowProcessInstanceService {

    /** 用户发起流程（通用审批，P1），返回实例 ID */
    String createProcessInstance(Long startUserId, CreateReq reqVO);

    PageResult<Instance> getMyProcessInstancePage(Long userId, PageParam pageParam, String name,
                                                  String processDefinitionKey, String category, Integer status);

    PageResult<Instance> getManagerProcessInstancePage(PageParam pageParam, String name,
                                                       String processDefinitionKey, String category, Integer status);

    Instance getProcessInstance(String id);

    ApprovalDetail getApprovalDetail(String id, String taskId);

    BpmnModelView getBpmnModelView(String id);

    /** 预测流程的下一审批节点（发起前校验用） */
    List<NextApprovalNode> getNextApprovalNodes(String processDefinitionId, String activityId,
                                                Map<String, Object> variables);

    void cancelProcessInstanceByStartUser(Long userId, String id, String reason);

    void cancelProcessInstanceByAdmin(Long userId, String id, String reason);

    /** 抄送我的分页 */
    PageResult<FlowProcessInstanceCopyDO> getProcessInstanceCopyPage(Long userId, PageParam pageParam,
                                                                     String processInstanceName);

    // ========== 供告警触发等内部使用 ==========

    /**
     * 启动流程实例（含多实例候选人预解析、实例命名）
     *
     * @param startUserId              发起人
     * @param processDefinitionIdOrKey 定义 ID 或 key（key 取最新版本）
     * @param businessKey              业务键（告警流程为 alert:{alertId}）
     * @param instanceName             实例名称
     * @param variables                流程变量
     * @param startUserSelectAssignees 发起人自选审批人 Map<nodeId, List<userId>>
     * @return 流程实例 ID
     */
    String startProcess(Long startUserId, String processDefinitionIdOrKey, String businessKey,
                        String instanceName, Map<String, Object> variables,
                        Map<String, List<Long>> startUserSelectAssignees);

}
