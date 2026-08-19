package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

@TableName("device_media_binding")
@KeySequence("device_media_binding_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceMediaBindingDO extends BaseDO {

    @TableId
    private Long id;

    private String deviceId;

    private Long srsLiveNodeId;

    private Long srsAiNodeId;

    private Long zlmNodeId;

    private String rtmpStream;

    private String httpStream;

    private String aiRtmpStream;

    private String aiHttpStream;

    private String zlmHost;

    private Integer zlmHttpPort;

    private Integer zlmRtmpPort;

    private String region;

    private String status;

}
