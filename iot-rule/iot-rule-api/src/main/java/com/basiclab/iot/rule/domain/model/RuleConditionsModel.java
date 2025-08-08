package com.basiclab.iot.rule.domain.model;


import lombok.Data;

import java.time.LocalDateTime;
@Data
public class RuleConditionsModel {

    private Long id;
    private Long ruleId;
    private Integer conditionType;

    private String conditionScheme;

    private LocalDateTime createTime;

    private String createBy;

    private String updateBy;
    private LocalDateTime updateTime;

    private static final long serialVersionUID = 1L;
}
