package com.basiclab.iot.message.sendlogic.msgmaker;

import com.basiclab.iot.message.domain.entity.TMsgDing;
import com.basiclab.iot.message.mapper.TMsgDingMapper;
import com.basiclab.iot.message.sendlogic.msgsender.DingMsgSender;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 钉钉消息加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2023-07-18
 */
@Component
public class DingMsgMaker extends BaseMsgMaker implements IMsgMaker {

    public static String agentId;

    public static String msgType;

    private static String msgTitle;

    private static String picUrl;

    public static String desc;

    public static String url;

    private static String btnTxt;

    private static String btnUrl;

    private static String msgContent;

    public static String radioType;

    public static String webHook;

    @Autowired
    private TMsgDingMapper tMsgDingMapper;

    /**
     * 准备(界面字段等)
     */
    @Override
    public void prepare() {
        String agentIdBefore = agentId;
        String agentIdNow = "";

        String webHookBefore = webHook;
        String webHookNow = "";
        synchronized (this) {
            if (agentIdBefore == null || !agentIdBefore.equals(agentIdNow)) {
                agentId = agentIdNow;
                DingMsgSender.accessTokenTimedCache = null;
            }
            if (webHookBefore == null || !webHookBefore.equals(webHookNow)) {
                DingMsgSender.robotClient = null;
            }
        }
        msgType = "";
        msgTitle ="";
        picUrl = "";
        url = "";
        btnTxt = "";
        btnUrl = "";
        msgContent ="";
//        if (DingMsgForm.getInstance().getWorkRadioButton().isSelected()) {
//            radioType = "work";
//        } else {
//            radioType = "robot";
//        }
        webHook = "";
    }

    /**
     * 组织消息-钉钉
     *
     * @param msgId 消息数据
     * @return TMsgDing
     */
    @Override
    public TMsgDing makeMsg(String msgId) {
        TMsgDing tMsgDing = tMsgDingMapper.selectByPrimaryKey(msgId);
        return tMsgDing;
    }
}
