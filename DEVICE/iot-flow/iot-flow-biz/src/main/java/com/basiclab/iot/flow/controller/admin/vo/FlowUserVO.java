package com.basiclab.iot.flow.controller.admin.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

/**
 * 流程用户精简 VO（审批人 / 发起人展示）
 */
@Schema(description = "管理后台 - FLOW 用户精简 VO")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class FlowUserVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    private String nickname;

}
