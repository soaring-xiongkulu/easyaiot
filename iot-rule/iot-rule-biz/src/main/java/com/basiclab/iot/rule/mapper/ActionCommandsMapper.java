package com.basiclab.iot.rule.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
* @description: ${description}
* @packagename: com.mqttsnet.iot.rule.mapper
* @author EasyIoT
* @date: 2025-12-04 21:39
**/
@Mapper
public interface ActionCommandsMapper  extends BaseMapper<RuleActionCommands> {
    /**
     * delete by primary key
     * @param id primaryKey
     * @return deleteCount
     */
    int deleteByPrimaryKey(Integer id);

    /**
     * insert record to table
     * @param record the record
     * @return insert count
     */
    int insert(RuleActionCommands record);

    int insertOrUpdate(RuleActionCommands record);

    int insertOrUpdateSelective(RuleActionCommands record);

    /**
     * insert record to table selective
     * @param record the record
     * @return insert count
     */
    int insertSelective(RuleActionCommands record);

    /**
     * select by primary key
     * @param id primary key
     * @return object by primary key
     */
    RuleActionCommands selectByPrimaryKey(Integer id);

    /**
     * update record selective
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKeySelective(RuleActionCommands record);

    /**
     * update record
     * @param record the updated record
     * @return update count
     */
    int updateByPrimaryKey(RuleActionCommands record);

    int updateBatch(List<RuleActionCommands> list);

    int updateBatchSelective(List<RuleActionCommands> list);

    int batchInsert(@Param("list") List<RuleActionCommands> list);

    List<RuleActionCommands> selectByActionCommandsSelective(RuleActionCommands ruleActionCommands);

    List<RuleActionCommands> actionCommandsByRuleId(@Param("ruleId")String ruleId);

    int deleteBatchByIds(Long[] ids);
}