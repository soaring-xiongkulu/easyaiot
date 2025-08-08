package com.basiclab.iot.rule.domain.model;


import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ActionCommandsModel {


    private Long id;


    private Integer actionType;

    private String ruleId;
    private String ruleConditionId;
    private String productIdentification;
    private String productName;

    private String deviceIdentificaiton;
    private String deviceName;

    private Object actionContent;

    private LocalDateTime createTime;

    private String createBy;

    private String updateBy;
    private LocalDateTime updateTime;


}
