package com.basiclab.iot.stream.task.platformStatus;

import com.basiclab.iot.stream.bean.SipTransactionInfo;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;

/**
 * 平台注册任务可序列化的信息
 */
@Slf4j
@Data
public class PlatformRegisterTaskInfo{

    private String platformServerId;

    private SipTransactionInfo sipTransactionInfo;

    /**
     * 过期时间
     */
    private long expireTime;
}
