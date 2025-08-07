package com.basiclab.iot.stream.task.deviceSubscribe;

import com.basiclab.iot.stream.bean.SipTransactionInfo;
import lombok.Data;

@Data
public class SubscribeTaskInfo {

    private String deviceId;

    private SipTransactionInfo transactionInfo;

    private String name;

    private String key;

    /**
     * 过期时间
     */
    private long expireTime;

}
