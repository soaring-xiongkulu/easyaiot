package com.basiclab.iot.flow.controller.admin.processinstance;

import com.basiclab.iot.flow.controller.admin.vo.FlowUserVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 流程实例 VO 集合（与前端 FlowProcessInstanceVO / 聚合接口对齐）
 */
public class FlowProcessInstanceVOs {

    private FlowProcessInstanceVOs() {
    }

    /** 流程实例 */
    @Schema(description = "管理后台 - 流程实例 VO")
    @Data
    public static class Instance implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String name;
        private Long startUserId;
        private String startUserNickname;
        private String processDefinitionId;
        private String processDefinitionKey;
        private String processDefinitionName;
        private String categoryId;
        /** 1 审批中 / 2 审批通过 / 3 审批不通过 / 4 已取消 */
        private Integer status;
        private String reason;
        private String businessKey;
        /** 当前节点名称（审批中）/ 最后节点（已结束） */
        private String taskName;
        private Date startTime;
        private Date endTime;
        private Long durationInMillis;
        private Map<String, Object> processVariables;

    }

    /** 审批详情聚合（detail 页） */
    @Schema(description = "管理后台 - 审批详情聚合 VO")
    @Data
    public static class ApprovalDetail implements Serializable {

        private static final long serialVersionUID = 1L;

        private Instance processInstance;
        /** 按节点分组的时间线（顺序 = 任务创建顺序） */
        private List<ActivityNode> activityNodes;

    }

    /** 时间线节点 */
    @Schema(description = "审批时间线节点")
    @Data
    public static class ActivityNode implements Serializable {

        private static final long serialVersionUID = 1L;

        /** 节点 ID（taskDefinitionKey） */
        private String id;
        private String name;
        /** 节点类型（对齐 Simple NodeType：11 审批等） */
        private Integer nodeType;
        private List<TaskItem> tasks;

    }

    /** 时间线任务 */
    @Schema(description = "审批时间线任务")
    @Data
    public static class TaskItem implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String name;
        private FlowUserVO assigneeUser;
        /** -2 跳过 / 0 待审批 / 1 审批中(多实例) / 2 通过 / 3 拒绝 / 4 已取消 / 5 已退回 / 7 审批中 */
        private Integer status;
        private String reason;
        private Date createTime;
        private Date endTime;

    }

    /** Simple 模型运行视图（查看器染色） */
    @Schema(description = "管理后台 - Simple 模型运行视图")
    @Data
    public static class BpmnModelView implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String name;
        private String processDefinitionId;
        /** Simple 设计器 JSON 树 */
        private Object simpleModel;
        /** 已通过节点 ID 集合 */
        private List<String> finishedTaskActivityIds;
        /** 已拒绝节点 ID 集合 */
        private List<String> rejectedTaskActivityIds;
        /** 进行中节点 ID 集合 */
        private List<String> unfinishedTaskActivityIds;

    }

    /** 下一审批节点预测 */
    @Schema(description = "下一审批节点")
    @Data
    public static class NextApprovalNode implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String name;
        private Integer nodeType;
        private List<FlowUserVO> candidateUsers;

    }

    /** 发起请求 */
    @Schema(description = "管理后台 - 流程发起 Request VO")
    @Data
    public static class CreateReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String processDefinitionId;
        private String processDefinitionKey;
        private Map<String, Object> variables;
        /** 发起人自选审批人：Map<nodeId, List<userId>> */
        private Map<String, List<Long>> startUserSelectAssignees;

    }

    /** 取消请求 */
    @Schema(description = "管理后台 - 流程取消 Request VO")
    @Data
    public static class CancelReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String reason;

    }

}
