package com.basiclab.iot.broker.domain.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-07
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@EqualsAndHashCode
@Builder
@ApiModel(value = "KafkaMessageRequestVO", description = "kafka 发送消息VO")
public class KafkaMessageRequestVO implements Serializable {

    private static final long serialVersionUID = 1L;


    @ApiModelProperty(value = "消息主题", required = true, example = "exampleTopic")
    private String topic;


    @ApiModelProperty(value = "消息数据", required = true)
    private String message;

}
