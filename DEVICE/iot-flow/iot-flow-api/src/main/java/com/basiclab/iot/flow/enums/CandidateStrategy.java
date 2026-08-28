package com.basiclab.iot.flow.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 候选人策略（与前端 consts.ts CandidateStrategy 一致）
 */
@Getter
@AllArgsConstructor
public enum CandidateStrategy {

    ROLE(10, "指定角色"),
    DEPT_MEMBER(20, "部门成员"),
    DEPT_LEADER(21, "部门负责人"),
    POST(22, "指定岗位"),
    USER(30, "指定成员"),
    APPROVE_USER_SELECT(34, "审批人自选"),
    START_USER_SELECT(35, "发起人自选"),
    START_USER(36, "发起人本人"),
    START_USER_DEPT_LEADER(37, "发起人部门负责人"),
    USER_GROUP(40, "指定用户组");

    private final Integer strategy;
    private final String name;

}
