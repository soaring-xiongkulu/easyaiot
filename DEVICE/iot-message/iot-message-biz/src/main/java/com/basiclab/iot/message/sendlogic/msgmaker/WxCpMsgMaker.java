package com.basiclab.iot.message.sendlogic.msgmaker;

import com.basiclab.iot.message.domain.entity.TMsgWxCp;
import com.basiclab.iot.message.mapper.TMsgWxCpMapper;
import me.chanjar.weixin.cp.bean.article.NewArticle;
import me.chanjar.weixin.cp.bean.message.WxCpMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 企业微信消息加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class WxCpMsgMaker extends BaseMsgMaker implements IMsgMaker {

    private static String agentId;

    public static String msgType;

    private static String msgTitle;

    private static String picUrl;

    public static String desc;

    public static String url;

    private static String btnTxt;

    private static String msgContent;

    @Autowired
    private TMsgWxCpMapper tMsgWxCpMapper;

    /**
     * 准备(界面字段等)
     */
    @Override
    public void prepare() {
        String agentIdBefore = agentId;
        String agentIdNow = "";
        synchronized (this) {
            if (agentIdBefore == null || !agentIdBefore.equals(agentIdNow)) {
                agentId = agentIdNow;
            }
        }
        msgType = "";
        msgTitle = "";
        picUrl = "";
        desc = "";
        url = "";
        btnTxt = "";
        msgContent = "";
    }

    /**
     * 组织消息-企业微信
     *
     * @param msgId 消息数据
     * @return WxMpTemplateMessage
     */
    @Override
    public WxCpMessage makeMsg(String msgId) {

        WxCpMessage wxCpMessage = null;

        TMsgWxCp tMsgWxCp = tMsgWxCpMapper.selectByPrimaryKey(msgId);
        wxCpMessage.setToUser(tMsgWxCp.getPreviewUser());
        String msgType = tMsgWxCp.getCpMsgType();
        if ("图文消息".equals(msgType)) {
            NewArticle article = new NewArticle();

            // 标题
            String title = tMsgWxCp.getTitle();
            article.setTitle(title);

            // 图片url
            article.setPicUrl(tMsgWxCp.getImgUrl());

            // 描述
            String description = tMsgWxCp.getDescribe();
            article.setDescription(description);

            // 跳转url
            article.setUrl(tMsgWxCp.getUrl());

            wxCpMessage = WxCpMessage.NEWS().addArticle(article).build();
        } else if ("文本消息".equals(msgType)) {
            String content = tMsgWxCp.getContent();
            wxCpMessage = WxCpMessage.TEXT().agentId(Integer.valueOf(tMsgWxCp.getAgentId())).toUser(tMsgWxCp.getPreviewUser()).content(content).build();
        } else if ("markdown消息".equals(msgType)) {
            String content = tMsgWxCp.getContent();
            wxCpMessage = WxCpMessage.MARKDOWN().agentId(Integer.valueOf(tMsgWxCp.getAgentId())).toUser(tMsgWxCp.getPreviewUser()).content(content).build();
        } else if ("文本卡片消息".equals(msgType)) {
            // 标题
            String title = tMsgWxCp.getTitle();
            // 描述
            String description = tMsgWxCp.getDescribe();
            // 跳转url
            String urlLink = tMsgWxCp.getUrl();
            wxCpMessage = WxCpMessage.TEXTCARD().agentId(Integer.valueOf(tMsgWxCp.getAgentId())).toUser(tMsgWxCp.getPreviewUser()).title(title)
                    .description(description).url(urlLink).btnTxt(tMsgWxCp.getBtnTxt()).build();
        }

        return wxCpMessage;
    }
}
