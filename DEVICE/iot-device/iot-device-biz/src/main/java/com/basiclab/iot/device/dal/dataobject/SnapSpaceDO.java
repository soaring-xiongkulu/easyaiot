package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

/**
 * SnapSpaceDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("video_snap_space")
@KeySequence("video_snap_space_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SnapSpaceDO extends BaseEntity {

    /**
     * 主键id
     */
    @TableId
    private Long id;
    /**
     * 空间名称
     */
    private String spaceName;
    /**
     * 抓拍空间编号
     */
    private String snapSpaceIdentification;
    /**
     * 文件保存模式[0:标准存储,1:归档存储]
     */
    private Integer saveMode;
    /**
     * 文件保存时间[0:永久保存,>=7(单位:天)]
     */
    private Integer saveTime;
    /**
     * 创建人
     */
    private String createBy;
    /**
     * 创建人
     */
    private String updateBy;

}