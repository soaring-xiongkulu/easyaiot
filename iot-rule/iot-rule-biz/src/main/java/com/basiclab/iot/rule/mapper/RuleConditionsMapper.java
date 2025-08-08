package com.basiclab.iot.rule.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.rule.domain.RuleConditions;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * @program: basiclab
 * @description: ${description}
 * @packagename: com.mqttsnet.iot.rule.mapper
 * @Author: Basiclab
 * @e-mainl: 853017739@qq.com
 * @date: 2024-07-21 18:50
 **/
@Mapper
public interface RuleConditionsMapper extends BaseMapper<RuleConditions> {
    /**
     * delete by primary key
     *
     * @param id primaryKey
     * @return deleteCount
     */
    int deleteByPrimaryKey(Long id);

    /**
     * insert record to table
     *
     * @param record the record
     * @return insert count
     */
    int insert(RuleConditions record);

    int insertOrUpdate(RuleConditions record);

    int insertOrUpdateSelective(RuleConditions record);

    /**
     * insert record to table selective
     *
     * @param record the record
     * @return insert count
     */
    int insertSelective(RuleConditions record);

    /**
     * select by primary key
     *
     * @param id primary key
     * @return object by primary key
     */
    RuleConditions selectByPrimaryKey(Long id);

    /**
     * 根据规则id查询规则条件集合
     *
     * @param ruleId
     * @return
     */
    List<RuleConditions> selectByRuleId(Long ruleId);

    /**
     * update record selective
     *
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKeySelective(RuleConditions record);

    /**
     * update record
     *
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKey(RuleConditions record);

    int updateBatchA(List<RuleConditions> list);

    int updateBatchSelective(List<RuleConditions> list);

    int batchInsert(@Param("list") List<RuleConditions> list);

    int deleteBatchByIds(Long[] ids);
}
