package com.basiclab.iot.flow.controller.admin.definition.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 流程定义 VO（与前端 FlowDefinitionVO 对齐）
 */
@Schema(description = "管理后台 - 流程定义 VO")
@Data
public class FlowDefinitionRespVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private String id;
    private String key;
    private String name;
    private Integer version;
    private String category;
    private String description;
    /** 1 激活 / 2 挂起 */
    private Integer suspensionState;
    private Date deploymentTime;

}
