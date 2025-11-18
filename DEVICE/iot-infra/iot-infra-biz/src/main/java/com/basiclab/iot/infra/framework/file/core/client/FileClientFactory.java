package com.basiclab.iot.infra.framework.file.core.client;

import com.basiclab.iot.infra.framework.file.core.enums.FileStorageEnum;

/**
 * FileClientFactory
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface FileClientFactory {

    FileClient getFileClient(Long configId);

    /**
     * 创建文件客户端
     *
     * @param configId 配置编号
     * @param storage  存储器的枚举 {@link FileStorageEnum}
     * @param config   文件配置
     */
    <Config extends FileClientConfig> void createOrUpdateFileClient(Long configId, Integer storage, Config config);

}
