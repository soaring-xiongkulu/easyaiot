package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "节点媒体根目录列表结果")
@Data
public class NodeStorageFileListRespVO {

    @Schema(description = "媒体挂载根绝对路径")
    private String mountRoot;

    @Schema(description = "当前相对路径（空表示根）")
    private String relativePath;

    @Schema(description = "当前绝对路径")
    private String absolutePath;

    private List<NodeStorageFileEntryVO> entries = new ArrayList<>();
}
