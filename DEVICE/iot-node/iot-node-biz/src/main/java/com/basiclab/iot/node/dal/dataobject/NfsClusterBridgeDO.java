package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.time.LocalDateTime;

@TableName("nfs_cluster_bridge")
@KeySequence("nfs_cluster_bridge_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NfsClusterBridgeDO extends BaseDO {

    @TableId
    private Long id;

    private String name;

    private Long sourceClusterId;

    private Long targetClusterId;

    /** 逗号分隔相对路径，如 alert_images,playbacks,snaps */
    private String sourceRelPaths;

    /** 目标相对路径前缀；空则 _bridge/{sourceClusterId} */
    private String targetRelPath;

    /** 可选 cron；空表示仅手动 */
    private String scheduleCron;

    private Boolean enabled;

    /** idle|running|stopped|error */
    private String status;

    private LocalDateTime lastRunAt;

    private Boolean lastSuccess;

    private String lastMessage;
}
