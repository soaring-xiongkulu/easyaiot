package com.basiclab.iot.flow.service.group;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.exception.util.ServiceExceptionUtil;
import com.basiclab.iot.flow.dal.dataobject.FlowUserGroupDO;
import com.basiclab.iot.flow.dal.pgsql.FlowUserGroupMapper;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.USER_GROUP_NOT_EXISTS;

/**
 * 审批用户组 Service 实现类
 */
@Service
public class FlowUserGroupServiceImpl implements FlowUserGroupService {

    @Resource
    private FlowUserGroupMapper userGroupMapper;

    @Override
    public Long createUserGroup(String name, String description, List<Long> memberUserIds, Integer status) {
        FlowUserGroupDO group = new FlowUserGroupDO();
        group.setName(name);
        group.setDescription(description);
        group.setMemberUserIds(memberUserIds);
        group.setStatus(status == null ? 0 : status);
        userGroupMapper.insert(group);
        return group.getId();
    }

    @Override
    public void updateUserGroup(Long id, String name, String description, List<Long> memberUserIds, Integer status) {
        getUserGroup(id);
        FlowUserGroupDO group = new FlowUserGroupDO();
        group.setId(id);
        group.setName(name);
        group.setDescription(description);
        group.setMemberUserIds(memberUserIds);
        group.setStatus(status);
        userGroupMapper.updateById(group);
    }

    @Override
    public void deleteUserGroup(Long id) {
        getUserGroup(id);
        userGroupMapper.deleteById(id);
    }

    @Override
    public FlowUserGroupDO getUserGroup(Long id) {
        FlowUserGroupDO group = userGroupMapper.selectById(id);
        if (group == null) {
            throw ServiceExceptionUtil.exception(USER_GROUP_NOT_EXISTS);
        }
        return group;
    }

    @Override
    public PageResult<FlowUserGroupDO> getUserGroupPage(PageParam pageParam, String name, Integer status) {
        return userGroupMapper.selectPage(pageParam, name, status);
    }

    @Override
    public List<FlowUserGroupDO> getUserGroupSimpleList() {
        return userGroupMapper.selectSimpleList();
    }

}
