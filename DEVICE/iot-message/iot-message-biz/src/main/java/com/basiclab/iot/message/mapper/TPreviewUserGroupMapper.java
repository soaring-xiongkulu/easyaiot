package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TPreviewUserGroup;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@Mapper
public interface TPreviewUserGroupMapper {

    int add(TPreviewUserGroup tPreviewUserGroup);

    int update(TPreviewUserGroup tPreviewUserGroup);

    int delete(String id);

    List<TPreviewUserGroup> selectList(TPreviewUserGroup tPreviewUserGroup);

    List<TPreviewUserGroup> queryByMsgType(int msgType);

    String queryPreviewUserIds(String id);

    String getGroupNameById(String id);

    Integer getGroupCount(String userGroupName);
}
