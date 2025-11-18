package com.basiclab.iot.sink.dal.dataobject;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

import java.time.LocalDateTime;

/**
 * ProductScriptDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@TableName("product_script")
@Data
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductScriptDO {

    /**
     * 主键ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 产品ID，关联product表
     */
    private Long productId;

    /**
     * 产品标识，冗余字段，便于查询
     */
    private String productIdentification;

    /**
     * 是否启用脚本，默认不启用
     */
    private Boolean scriptEnabled;

    /**
     * 脚本内容，包含rawDataToProtocol和protocolToRawData两个函数
     */
    private String scriptContent;

    /**
     * 脚本版本号，用于版本控制
     */
    private Integer scriptVersion;

    /**
     * 创建者
     */
    private String createBy;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新者
     */
    private String updateBy;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

    /**
     * 租户编号
     */
    private Long tenantId;
}

