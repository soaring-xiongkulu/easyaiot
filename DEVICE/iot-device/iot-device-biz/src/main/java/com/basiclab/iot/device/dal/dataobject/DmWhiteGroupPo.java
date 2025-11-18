package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * DmWhiteGroupPo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_white_group")
@KeySequence("device_ota_white_group_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmWhiteGroupPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = -9064738268095232039L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 测试白名单组名
     */
    private String groupName;
    /**
     * 产品ID
     */
    private String productIdentification;
}
