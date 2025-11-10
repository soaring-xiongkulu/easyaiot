package com.basiclab.iot.dataset.enums.dataset;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 数据集审批状态
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2024-10-22
 */
@Getter
@AllArgsConstructor
public enum DatasetAudit {

    /**
     * 待审核
     */
    PENDING_APPROVAL(0, "PENDING_APPROVAL"),

    /**
     * 审核通过
     */
    APPROVED(1, "APPROVED"),

    /**
     * 审核驳回
     */
    REJECT(2, "REJECT");

    private Integer key;
    private String value;

}
