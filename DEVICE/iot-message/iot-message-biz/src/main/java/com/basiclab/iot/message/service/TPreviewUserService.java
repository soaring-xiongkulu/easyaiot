package com.basiclab.iot.message.service;


import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.TPreviewUser;

import java.util.List;

public interface TPreviewUserService {
    AjaxResult add(TPreviewUser tPreviewUser);

    TPreviewUser update(TPreviewUser tPreviewUser);

    String delete(String id);

    List<TPreviewUser> query(TPreviewUser tPreviewUser);

    List<TPreviewUser> queryByMsgType(int msgType);
}
