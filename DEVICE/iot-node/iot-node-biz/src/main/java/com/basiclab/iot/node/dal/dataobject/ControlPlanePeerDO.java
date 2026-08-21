package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.time.LocalDateTime;

@TableName(value = "control_plane_peer", autoResultMap = true)
@KeySequence("control_plane_peer_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ControlPlanePeerDO extends BaseDO {

    @TableId
    private Long id;

    private String name;

    private String apiBaseUrl;

    private String host;

    private String peerToken;

    private String status;

    private Long remotePlatformNodeId;

    private LocalDateTime lastSyncAt;

    private String remark;

}
