package com.basiclab.iot.message.sendlogic.msgmaker;

import com.basiclab.iot.message.domain.entity.TMsgFeishu;
import com.basiclab.iot.message.mapper.TMsgFeishuMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 飞书消息加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-12-04
 */
@Component
public class FeishuMsgMaker extends BaseMsgMaker implements IMsgMaker {

    @Autowired
    private TMsgFeishuMapper tMsgFeishuMapper;

    /**
     * 准备(界面字段等)
     */
    @Override
    public void prepare() {
        // 初始化准备逻辑
    }

    /**
     * 组织消息
     *
     * @param msgId 消息ID
     * @return TMsgFeishu
     */
    @Override
    public TMsgFeishu makeMsg(String msgId) {
        TMsgFeishu tMsgFeishu = tMsgFeishuMapper.selectByPrimaryKey(msgId);
        return tMsgFeishu;
    }
}

