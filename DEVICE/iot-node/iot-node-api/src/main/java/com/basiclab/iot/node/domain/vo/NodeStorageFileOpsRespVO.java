package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "节点媒体文件运维操作结果")
@Data
public class NodeStorageFileOpsRespVO {

    private Boolean success;
    private String message;
    /** 操作后相对路径（新建目录/上传文件） */
    private String relativePath;
}
