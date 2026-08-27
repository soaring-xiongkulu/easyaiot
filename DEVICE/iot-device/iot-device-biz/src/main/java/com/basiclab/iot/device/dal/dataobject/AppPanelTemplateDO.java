package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;

import java.io.Serializable;

/**
 * AppPanelTemplateDO
 *
 * App 控制面板模板：云端定制每个产品在 APP 内展示的控制页面，
 * 模板绑定产品后由 APP 按 productIdentification 拉取并动态渲染控制页。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("app_panel_template")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AppPanelTemplateDO extends BaseEntity2 implements Serializable {

    /**
     * 状态：草稿
     */
    public static final String STATUS_DRAFT = "DRAFT";

    /**
     * 状态：已发布
     */
    public static final String STATUS_PUBLISHED = "PUBLISHED";

    /**
     * 状态：停用
     */
    public static final String STATUS_DISABLED = "DISABLED";

    /**
     * 主键ID
     */
    @TableId(type = IdType.AUTO)
    @ApiModelProperty(value = "主键ID")
    private Long id;

    /**
     * 模板编码：全局唯一，App 可按编码兜底取默认模板
     */
    @ApiModelProperty(value = "模板编码")
    private String templateCode;

    /**
     * 模板名称
     */
    @ApiModelProperty(value = "模板名称")
    private String templateName;

    /**
     * 绑定产品标识（对应 product.product_identification）
     */
    @ApiModelProperty(value = "绑定产品标识")
    private String productIdentification;

    /**
     * 状态：DRAFT-草稿，PUBLISHED-已发布，DISABLED-停用
     */
    @ApiModelProperty(value = "状态：DRAFT-草稿，PUBLISHED-已发布，DISABLED-停用")
    private String status;

    /**
     * 版本号，每次发布自增
     */
    @ApiModelProperty(value = "版本号，每次发布自增")
    private Integer version;

    /**
     * 面板模板 JSON：pages[{name,widgets[{id,type,title,...}]}]
     */
    @ApiModelProperty(value = "面板模板 JSON")
    private String panelSchema;

    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;

    /**
     * 租户编号
     */
    @ApiModelProperty(value = "租户编号")
    private Long tenantId;

    /**
     * 是否删除：0-未删除，1-已删除
     */
    @TableLogic
    @ApiModelProperty(value = "是否删除：0-未删除，1-已删除")
    private Integer deleted;
}
