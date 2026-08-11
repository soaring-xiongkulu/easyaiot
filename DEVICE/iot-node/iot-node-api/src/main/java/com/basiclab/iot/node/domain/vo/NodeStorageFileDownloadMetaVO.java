package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "节点媒体文件下载元信息（实际内容由 download 接口流式返回）")
@Data
public class NodeStorageFileDownloadMetaVO {

    private String fileName;
    private Long size;
    private String contentType;
}
