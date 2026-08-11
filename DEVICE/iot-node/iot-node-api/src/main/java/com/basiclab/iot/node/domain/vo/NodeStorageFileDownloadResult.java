package com.basiclab.iot.node.domain.vo;

import lombok.Data;

/**
 * 内部下载结果（控制器转成 HTTP 附件）
 */
@Data
public class NodeStorageFileDownloadResult {

    private String fileName;
    private long size;
    private byte[] content;
}
