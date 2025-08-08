package com.basiclab.iot.rule.domain.model;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class RuleModel {
    private static final long serialVersionUID = 1L;
    private Long id;
    private String appId;
    private Integer conditionType;
    private String ruleIdentification;
    private String ruleName;
    private String cronExpression;
    private String misfirePolicy;
    private String concurrent;
    private String jobIdentification;
    private String status;
    private String remark;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    private List<RuleConditionsModel> ruleConditionsModelList;

    private List<ActionCommandsModel> actionCommandsModelList;

}
