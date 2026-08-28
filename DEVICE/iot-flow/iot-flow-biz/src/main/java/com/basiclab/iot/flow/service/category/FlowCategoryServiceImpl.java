package com.basiclab.iot.flow.service.category;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.exception.util.ServiceExceptionUtil;
import com.basiclab.iot.flow.controller.admin.category.vo.FlowCategoryVO;
import com.basiclab.iot.flow.dal.dataobject.FlowCategoryDO;
import com.basiclab.iot.flow.dal.pgsql.FlowCategoryMapper;
import org.flowable.engine.RepositoryService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.CATEGORY_EXISTS_CODE;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.CATEGORY_NOT_EXISTS;
import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.CATEGORY_USED_BY_MODEL;

/**
 * 流程分类 Service 实现类
 */
@Service
public class FlowCategoryServiceImpl implements FlowCategoryService {

    @Resource
    private FlowCategoryMapper categoryMapper;
    @Resource
    private RepositoryService repositoryService;

    @Override
    public Long createCategory(FlowCategoryVO reqVO) {
        validateCodeUnique(null, reqVO.getCode());
        FlowCategoryDO category = new FlowCategoryDO();
        category.setName(reqVO.getName());
        category.setCode(reqVO.getCode());
        category.setStatus(reqVO.getStatus() == null ? 0 : reqVO.getStatus());
        category.setSort(reqVO.getSort() == null ? 0 : reqVO.getSort());
        category.setDescription(reqVO.getDescription());
        categoryMapper.insert(category);
        return category.getId();
    }

    @Override
    public void updateCategory(FlowCategoryVO reqVO) {
        getCategory(reqVO.getId());
        validateCodeUnique(reqVO.getId(), reqVO.getCode());
        FlowCategoryDO category = new FlowCategoryDO();
        category.setId(reqVO.getId());
        category.setName(reqVO.getName());
        category.setCode(reqVO.getCode());
        category.setStatus(reqVO.getStatus());
        category.setSort(reqVO.getSort());
        category.setDescription(reqVO.getDescription());
        categoryMapper.updateById(category);
    }

    @Override
    public void deleteCategory(Long id) {
        FlowCategoryDO category = getCategory(id);
        // 被流程模型引用时禁止删除（模型分类存的就是 code）
        if (repositoryService.createModelQuery().modelCategory(category.getCode()).count() > 0) {
            throw ServiceExceptionUtil.exception(CATEGORY_USED_BY_MODEL);
        }
        categoryMapper.deleteById(id);
    }

    @Override
    public FlowCategoryDO getCategory(Long id) {
        FlowCategoryDO category = categoryMapper.selectById(id);
        if (category == null) {
            throw ServiceExceptionUtil.exception(CATEGORY_NOT_EXISTS);
        }
        return category;
    }

    @Override
    public PageResult<FlowCategoryDO> getCategoryPage(PageParam pageParam, String name, String code, Integer status) {
        return categoryMapper.selectPage(pageParam, name, code, status);
    }

    @Override
    public List<FlowCategoryDO> getCategorySimpleList() {
        return categoryMapper.selectSimpleList();
    }

    private void validateCodeUnique(Long id, String code) {
        FlowCategoryDO exists = categoryMapper.selectByCode(code);
        if (exists == null) {
            return;
        }
        if (id == null || !id.equals(exists.getId())) {
            throw ServiceExceptionUtil.exception(CATEGORY_EXISTS_CODE);
        }
    }

}
