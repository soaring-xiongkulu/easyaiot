package com.basiclab.iot.stream.common;

import com.basiclab.iot.stream.bean.SipTransactionInfo;

public interface DeviceStatusCallback {
    public void run(String deviceId, SipTransactionInfo transactionInfo);
}
