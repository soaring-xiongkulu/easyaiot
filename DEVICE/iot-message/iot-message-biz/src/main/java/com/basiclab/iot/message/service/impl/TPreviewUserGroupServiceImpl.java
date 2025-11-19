package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.TPreviewUser;
import com.basiclab.iot.message.domain.entity.TPreviewUserGroup;
import com.basiclab.iot.message.mapper.TPreviewUserGroupMapper;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.service.TPreviewUserGroupService;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * 用户组管理实现层impl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class TPreviewUserGroupServiceImpl implements TPreviewUserGroupService {

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Override
    public AjaxResult add(TPreviewUserGroup tPreviewUserGroup) {
        int count = tPreviewUserGroupMapper.getGroupCount(tPreviewUserGroup.getUserGroupName());
        if(count > 0){
            return AjaxResult.error(5000, "该消息类型下已存在重复用户组，请检查后重新输入！");
        }
        tPreviewUserGroup.setId(UUID.randomUUID().toString());
        tPreviewUserGroup.setCreateTime(new Date());
        tPreviewUserGroupMapper.add(tPreviewUserGroup);
        return AjaxResult.success(tPreviewUserGroup);
    }

    @Override
    public TPreviewUserGroup update(TPreviewUserGroup tPreviewUserGroup) {
        tPreviewUserGroupMapper.update(tPreviewUserGroup);
        return tPreviewUserGroup;
    }

    @Override
    public String delete(String id) {
        tPreviewUserGroupMapper.delete(id);
        return id;
    }

    @Override
    public List<TPreviewUserGroup> query(TPreviewUserGroup tPreviewUserGroup) {
        List<TPreviewUserGroup> tPreviewUserGroups = tPreviewUserGroupMapper.selectList(tPreviewUserGroup);
        for(TPreviewUserGroup previewUserGroup : CollectionUtils.emptyIfNull(tPreviewUserGroups)){
            String previewUserId = previewUserGroup.getPreviewUserId();
            if(StringUtils.isNotEmpty(previewUserId)){
                List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
                List<TPreviewUser> tPreviewUsers = tPreviewUserMapper.queryByIds(previewUserIds);
                previewUserGroup.setTPreviewUsers(tPreviewUsers);
            }
        }
        return tPreviewUserGroups;
    }

    @Override
    public List<TPreviewUserGroup> queryByMsgType(int msgType) {
        List<TPreviewUserGroup> tPreviewUserGroups = tPreviewUserGroupMapper.queryByMsgType(msgType);
        return tPreviewUserGroups;
    }
}
