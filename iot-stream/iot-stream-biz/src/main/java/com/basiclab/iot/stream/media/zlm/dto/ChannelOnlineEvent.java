package com.basiclab.iot.stream.media.zlm.dto;

import com.basiclab.iot.stream.bean.SendRtpInfo;

import java.text.ParseException;

/**
 * @author lin
 */
public interface ChannelOnlineEvent {

    void run(SendRtpInfo sendRtpItem) throws ParseException;
}
