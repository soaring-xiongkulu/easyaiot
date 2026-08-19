package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

@Schema(description = "边缘节点更新")
@Data
public class EdgeNodeUpdateReqVO {

    @NotNull
    private Long id;

    private String name;

    private String remark;

    private Integer maxTaskCount;

    private Boolean enabled;

}
