package com.basiclab.iot.node.domain.vo;

import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Schema(description = "边缘节点分页查询")
@Data
@EqualsAndHashCode(callSuper = true)
public class EdgeNodePageReqVO extends PageParam {

    private String name;

    private String host;

    private String status;

    private Boolean enabled;

}
