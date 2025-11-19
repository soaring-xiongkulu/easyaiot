package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.TPreviewUser;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.service.TPreviewUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * 目标用户实现层impl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class TPreviewUserServiceImpl implements TPreviewUserService {

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Override
    public AjaxResult add(TPreviewUser tPreviewUser) {
        int count = tPreviewUserMapper.getUserCount(tPreviewUser.getMsgType(),tPreviewUser.getPreviewUser());
        if(count > 0){

            return AjaxResult.error(500, "该消息类型已存在重复目标用户，请检查后重新输入！");
        }
        tPreviewUser.setId(UUID.randomUUID().toString());
        tPreviewUser.setCreateTime(new Date());
        tPreviewUserMapper.add(tPreviewUser);
        return AjaxResult.success(tPreviewUser);
    }

    @Override
    public TPreviewUser update(TPreviewUser tPreviewUser) {
        tPreviewUserMapper.update(tPreviewUser);
        return tPreviewUser;
    }

    @Override
    public String delete(String id) {
        tPreviewUserMapper.delete(id);
        return id;
    }

    @Override
    public  List<TPreviewUser>  query(TPreviewUser tPreviewUser) {
        return tPreviewUserMapper.selectList(tPreviewUser);
    }

    @Override
    public List<TPreviewUser> queryByMsgType(int msgType) {
        return tPreviewUserMapper.queryByMsgType(msgType);
    }
}
