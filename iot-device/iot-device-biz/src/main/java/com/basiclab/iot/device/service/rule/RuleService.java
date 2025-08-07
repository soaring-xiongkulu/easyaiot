package com.basiclab.iot.device.service.rule;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.rule.vo.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.device.dal.dataobject.rule.RuleDO;

/**
 * 规则信息 Service 接口
 *
 * @author BasicLab
 */
public interface RuleService {

    /**
     * 创建规则信息
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long create(@Valid RuleSaveReqVO createReqVO);

    /**
     * 更新规则信息
     *
     * @param updateReqVO 更新信息
     */
    void update(@Valid RuleSaveReqVO updateReqVO);

    /**
     * 删除规则信息
     *
     * @param id 编号
     */
    void delete(Long id);

    /**
     * 获得规则信息
     *
     * @param id 编号
     * @return 规则信息
     */
    RuleDO get(Long id);

    /**
     * 获得规则信息分页
     *
     * @param pageReqVO 分页查询
     * @return 规则信息分页
     */
    PageResult<RuleDO> getPage(RulePageReqVO pageReqVO);

}