package com.basiclab.iot.flow.service.category;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.controller.admin.category.vo.FlowCategoryVO;
import com.basiclab.iot.flow.dal.dataobject.FlowCategoryDO;

import java.util.List;

/**
 * 流程分类 Service 接口
 */
public interface FlowCategoryService {

    Long createCategory(FlowCategoryVO reqVO);

    void updateCategory(FlowCategoryVO reqVO);

    void deleteCategory(Long id);

    FlowCategoryDO getCategory(Long id);

    PageResult<FlowCategoryDO> getCategoryPage(PageParam pageParam, String name, String code, Integer status);

    /** 开启状态的精简列表（下拉） */
    List<FlowCategoryDO> getCategorySimpleList();

}
