package com.basiclab.iot.stream.task.deviceStatus;

import com.basiclab.iot.stream.bean.SipTransactionInfo;
import lombok.Data;

@Data
public class DeviceStatusTaskInfo{

    private String deviceId;

    private SipTransactionInfo transactionInfo;

    /**
     * 过期时间
     */
    private long expireTime;
}
