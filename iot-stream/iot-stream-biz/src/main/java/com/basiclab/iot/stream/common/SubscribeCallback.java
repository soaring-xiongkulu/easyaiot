package com.basiclab.iot.stream.common;

import com.basiclab.iot.stream.bean.SipTransactionInfo;

public interface SubscribeCallback{
    public void run(String deviceId, SipTransactionInfo transactionInfo);
}
