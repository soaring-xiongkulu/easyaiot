package com.basiclab.iot.transform.capability.backup;

import com.basiclab.iot.transform.core.envelope.TransformEnvelope;

/**
 * 备份能力：流转级镜像归档，独立 Group，不争抢业务投递。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface BackupCapability {

    void archive(TransformEnvelope envelope);
}
