package com.basiclab.iot.stream.service.bean;

import com.basiclab.iot.stream.bean.SendRtpInfo;


public class RequestStopPushStreamMsg {


    private SendRtpInfo sendRtpItem;


    private String platformName;


    private int platFormIndex;

    public SendRtpInfo getSendRtpItem() {
        return sendRtpItem;
    }

    public void setSendRtpItem(SendRtpInfo sendRtpItem) {
        this.sendRtpItem = sendRtpItem;
    }

    public String getPlatformName() {
        return platformName;
    }

    public void setPlatformName(String platformName) {
        this.platformName = platformName;
    }


    public int getPlatFormIndex() {
        return platFormIndex;
    }

    public void setPlatFormIndex(int platFormIndex) {
        this.platFormIndex = platFormIndex;
    }

    public static RequestStopPushStreamMsg getInstance(SendRtpInfo sendRtpItem, String platformName, int platFormIndex) {
        RequestStopPushStreamMsg streamMsg = new RequestStopPushStreamMsg();
        streamMsg.setSendRtpItem(sendRtpItem);
        streamMsg.setPlatformName(platformName);
        streamMsg.setPlatFormIndex(platFormIndex);
        return streamMsg;
    }
}
