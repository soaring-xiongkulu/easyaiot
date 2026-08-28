package com.basiclab.iot.flow.service.group;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowUserGroupDO;

import java.util.List;

/**
 * 审批用户组 Service 接口
 */
public interface FlowUserGroupService {

    Long createUserGroup(String name, String description, List<Long> memberUserIds, Integer status);

    void updateUserGroup(Long id, String name, String description, List<Long> memberUserIds, Integer status);

    void deleteUserGroup(Long id);

    FlowUserGroupDO getUserGroup(Long id);

    PageResult<FlowUserGroupDO> getUserGroupPage(PageParam pageParam, String name, Integer status);

    List<FlowUserGroupDO> getUserGroupSimpleList();

}
