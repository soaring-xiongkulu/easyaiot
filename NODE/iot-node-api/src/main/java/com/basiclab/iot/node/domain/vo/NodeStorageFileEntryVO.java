package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

@Schema(description = "节点媒体根目录文件条目")
@Data
public class NodeStorageFileEntryVO {

    private String name;
    private Boolean directory;
    private Long size;
    private LocalDateTime mtime;
    /** 相对媒体根的路径，如 playbacks/live */
    private String relativePath;
}
