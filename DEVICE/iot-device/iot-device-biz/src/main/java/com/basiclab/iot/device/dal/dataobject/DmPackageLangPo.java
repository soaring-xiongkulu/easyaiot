package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;

/**
 * DmPackageLangPo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("dm_ota_version_lang")
@KeySequence("dm_ota_version_lang_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackageLangPo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 6205359759492724306L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 包ID(dm_ota_pkg.id)
     */
    @TableField(value = "pkg_id")
    private Long pkgId;
    /**
     * 大版本号ID
     */
    @TableField(value = "version_id")
    private Long versionId;
    /**
     * 字段名,如:upgrade_desc
     */
    @TableField(value = "field_name")
    private String fieldName;
    /**
     * 字段值
     */
    @TableField(value = "field_value")
    private String fieldValue;

}
