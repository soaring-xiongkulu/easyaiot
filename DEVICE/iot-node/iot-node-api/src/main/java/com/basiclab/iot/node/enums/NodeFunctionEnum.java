package com.basiclab.iot.node.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum NodeFunctionEnum {

    ALGORITHM("algorithm", "视频分析"),
    FORWARD("forward", "推流转发"),
    LIVE("live", "直播接入"),
    TRAIN("train", "模型训练"),
    LLM("llm", "大模型"),
    LABEL("label", "智能标注"),
    INFER("infer", "模型推理"),
    MQTT("mqtt", "物联接入"),
    NFS("nfs", "共享存储"),
    TRANSFORM("transform", "数据转发");

    private final String id;
    private final String label;

    public static NodeFunctionEnum of(String id) {
        if (id == null || id.isBlank()) {
            return null;
        }
        String key = id.trim().toLowerCase();
        for (NodeFunctionEnum value : values()) {
            if (value.id.equals(key)) {
                return value;
            }
        }
        return null;
    }
}
