package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 数据仓数据集关联 DO
 *
 * @author IoT
 */
@TableName("warehouse_dataset")
@KeySequence("warehouse_dataset_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WarehouseDatasetDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 数据集ID
     */
    private Long datasetId;
    /**
     * 数据仓ID
     */
    private Long warehouseId;
    /**
     * 计划同步数量
     */
    private Integer planSyncCount;
    /**
     * 已同步数量
     */
    private Integer syncCount;
    /**
     * 同步状态[0:未同步,1:同步中,2:同步完成]
     */
    private Integer syncStatus;
    /**
     * 同步失败数量
     */
    private Integer failCount;

}