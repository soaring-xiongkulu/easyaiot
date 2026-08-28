package com.basiclab.iot.flow.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.flow.dal.dataobject.FlowCategoryDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 流程分类 Mapper
 */
@Mapper
public interface FlowCategoryMapper extends BaseMapperX<FlowCategoryDO> {

    default PageResult<FlowCategoryDO> selectPage(PageParam pageParam, String name, String code, Integer status) {
        return selectPage(pageParam, new LambdaQueryWrapperX<FlowCategoryDO>()
                .likeIfPresent(FlowCategoryDO::getName, name)
                .likeIfPresent(FlowCategoryDO::getCode, code)
                .eqIfPresent(FlowCategoryDO::getStatus, status)
                .orderByAsc(FlowCategoryDO::getSort)
                .orderByDesc(FlowCategoryDO::getId));
    }

    default List<FlowCategoryDO> selectSimpleList() {
        return selectList(new LambdaQueryWrapperX<FlowCategoryDO>()
                .eq(FlowCategoryDO::getStatus, 0)
                .orderByAsc(FlowCategoryDO::getSort));
    }

    default FlowCategoryDO selectByCode(String code) {
        return selectOne(FlowCategoryDO::getCode, code);
    }

}
