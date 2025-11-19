package com.basiclab.iot.message.domain.entity;

import lombok.Data;

import java.util.Map;

/**
 * 消息配置实体
 *
 */
@Data
public class MessageConfig {

    private String id;

    private String creatorId;

    private Long createTime;

    private int msgType;

    private String configuration;

    private Map<String,Object> configurationMap;

}
