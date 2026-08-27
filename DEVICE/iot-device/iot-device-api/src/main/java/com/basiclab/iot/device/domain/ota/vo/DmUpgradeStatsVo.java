package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.util.List;

/**
 * 升级统计（漏斗 + 健康度）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmUpgradeStatsVo对象", description = "升级统计")
public class DmUpgradeStatsVo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 命中设备数（去重）
     */
    @ApiModelProperty(value = "命中设备数（去重）")
    private Long checkHitCount;

    /**
     * 启动成功设备数（去重）
     */
    @ApiModelProperty(value = "启动成功设备数（去重）")
    private Long launchOkCount;

    /**
     * 覆盖率（启动成功 / 命中）
     */
    @ApiModelProperty(value = "覆盖率（启动成功/命中）")
    private Double coverage;

    /**
     * 成功率（安装结果中成功占比）
     */
    @ApiModelProperty(value = "成功率")
    private Double successRate;

    /**
     * 是否建议升阶
     */
    @ApiModelProperty(value = "是否建议升阶")
    private Boolean suggestPromote;

    /**
     * 建议升阶到的阶梯[1:设备级,2:产品级,3:全量]
     */
    @ApiModelProperty(value = "建议升阶到的阶梯")
    private Integer nextLadder;

    /**
     * 漏斗统计（各阶段设备数）
     */
    @ApiModelProperty(value = "漏斗统计（各阶段设备数）")
    private List<DmFunnelItemVo> funnel;

    /**
     * Top 错误码
     */
    @ApiModelProperty(value = "Top 错误码")
    private List<DmErrorTopVo> errorTops;

    @Data
    @ApiModel(value = "DmFunnelItemVo对象", description = "漏斗统计项")
    public static class DmFunnelItemVo implements Serializable {

        private static final long serialVersionUID = 1L;

        /**
         * 升级阶段
         */
        @ApiModelProperty(value = "升级阶段")
        private Integer phase;

        /**
         * 阶段名称
         */
        @ApiModelProperty(value = "阶段名称")
        private String phaseName;

        /**
         * 设备数（去重）
         */
        @ApiModelProperty(value = "设备数（去重）")
        private Long deviceCount;
    }

    @Data
    @ApiModel(value = "DmErrorTopVo对象", description = "错误码统计项")
    public static class DmErrorTopVo implements Serializable {

        private static final long serialVersionUID = 1L;

        /**
         * 错误码
         */
        @ApiModelProperty(value = "错误码")
        private String errorCode;

        /**
         * 错误信息
         */
        @ApiModelProperty(value = "错误信息")
        private String errorMsg;

        /**
         * 次数
         */
        @ApiModelProperty(value = "次数")
        private Long count;
    }
}
