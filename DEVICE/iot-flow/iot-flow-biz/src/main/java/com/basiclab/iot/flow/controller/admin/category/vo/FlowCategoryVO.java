package com.basiclab.iot.flow.controller.admin.category.vo;

import com.basiclab.iot.flow.dal.dataobject.FlowCategoryDO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import java.io.Serializable;

/**
 * 流程分类 VO（与前端 FlowCategoryVO 对齐）
 */
@Schema(description = "管理后台 - 流程分类 VO")
@Data
public class FlowCategoryVO implements Serializable {

    private static final long serialVersionUID = 1L;

    private Long id;
    @NotEmpty(message = "分类名称不能为空")
    private String name;
    @NotEmpty(message = "分类编码不能为空")
    private String code;
    /** 状态：0 开启 / 1 禁用 */
    private Integer status;
    private Integer sort;
    private String description;

    public static FlowCategoryVO of(FlowCategoryDO bean) {
        if (bean == null) {
            return null;
        }
        FlowCategoryVO vo = new FlowCategoryVO();
        vo.setId(bean.getId());
        vo.setName(bean.getName());
        vo.setCode(bean.getCode());
        vo.setStatus(bean.getStatus());
        vo.setSort(bean.getSort());
        vo.setDescription(bean.getDescription());
        return vo;
    }

}
