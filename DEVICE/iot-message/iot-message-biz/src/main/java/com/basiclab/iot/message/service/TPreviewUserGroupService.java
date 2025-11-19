package com.basiclab.iot.message.service;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.TPreviewUserGroup;

import java.util.List;

public interface TPreviewUserGroupService {
    AjaxResult add(TPreviewUserGroup tPreviewUserGroup);

    TPreviewUserGroup update(TPreviewUserGroup tPreviewUserGroup);

    String delete(String id);

    List<TPreviewUserGroup> query(TPreviewUserGroup tPreviewUserGroup);

    List<TPreviewUserGroup> queryByMsgType(int msgType);

}
