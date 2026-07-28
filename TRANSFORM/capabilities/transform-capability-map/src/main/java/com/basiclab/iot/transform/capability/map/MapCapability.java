package com.basiclab.iot.transform.capability.map;

import com.basiclab.iot.transform.core.envelope.TransformEnvelope;

/**
 * 映射能力：字段映射 / 脚本变换，面向 N 方业务载荷。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface MapCapability {

    TransformEnvelope map(String mappingId, TransformEnvelope source);
}
