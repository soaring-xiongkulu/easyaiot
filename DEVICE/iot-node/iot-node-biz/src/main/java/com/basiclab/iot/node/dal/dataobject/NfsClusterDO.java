package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

@TableName("nfs_cluster")
@KeySequence("nfs_cluster_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NfsClusterDO extends BaseDO {

    @TableId
    private Long id;

    private String name;

    /** local | peer-{id}，与控制面泳道 laneKey 对齐 */
    private String laneKey;

    private Long controlPlaneId;

    private Long primaryNodeId;

    private Long standbyNodeId;

    private String mountRoot;

    private String nfsExport;

    private String nfsMountOpts;

    /** 是否当前生效主集群（全局仅一个为 true） */
    private Boolean isActive;

    private String status;

    private String remark;
}
