package com.basiclab.iot.flow.controller.admin.task;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.flow.controller.admin.vo.FlowUserVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 任务 VO 集合（与前端 FlowTaskVO / 操作请求对齐）
 */
public class FlowTaskVOs {

    private FlowTaskVOs() {
    }

    /** 任务条目 */
    @Schema(description = "管理后台 - 流程任务 VO")
    @Data
    public static class TaskVO implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String name;
        private String processInstanceId;
        private String processInstanceName;
        private String processDefinitionKey;
        private String processDefinitionName;
        private FlowUserVO assigneeUser;
        private FlowUserVO ownerUser;
        /** -2 跳过 / 0 待审批 / 1 审批中(多实例) / 2 通过 / 3 拒绝 / 4 已取消 / 5 已退回 / 7 审批中 */
        private Integer status;
        private String reason;
        private Date createTime;
        private Date endTime;
        private Long durationInMillis;
        private FlowUserVO startUser;

    }

    /** 审批通过请求 */
    @Data
    public static class ApproveReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String reason;
        private Map<String, Object> variables;

    }

    /** 审批拒绝请求 */
    @Data
    public static class RejectReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String reason;

    }

    /** 退回请求 */
    @Data
    public static class ReturnReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String targetTaskDefinitionKey;
        private String reason;

    }

    /** 转办 / 委派请求 */
    @Data
    public static class AssignReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private Long assigneeUserId;
        private String reason;

    }

    /** 抄送请求 */
    @Data
    public static class CopyReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private List<Long> userIds;
        private String reason;

    }

    /** 加签请求 */
    @Data
    public static class CreateSignReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private List<Long> userIds;
        /** BEFORE / AFTER（M1 统一为父任务子任务） */
        private String type;
        private String reason;

    }

    /** 减签 / 撤回请求 */
    @Data
    public static class ReasonReq implements Serializable {

        private static final long serialVersionUID = 1L;

        private String id;
        private String reason;

    }

    /** 任务分页请求 */
    @Data
    public static class PageReq extends PageParam implements Serializable {

        private static final long serialVersionUID = 1L;

        private String name;
        private String processInstanceName;

    }

}
