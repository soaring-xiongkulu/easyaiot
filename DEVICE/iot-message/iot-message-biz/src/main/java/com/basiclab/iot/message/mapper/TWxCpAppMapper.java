package com.basiclab.iot.message.mapper;




import com.basiclab.iot.message.domain.entity.TWxCpApp;

import java.util.List;

public interface TWxCpAppMapper {
    int deleteByPrimaryKey(Integer id);

    int insert(TWxCpApp record);

    int insertSelective(TWxCpApp record);

    TWxCpApp selectByPrimaryKey(Integer id);

    int updateByPrimaryKeySelective(TWxCpApp record);

    int updateByPrimaryKey(TWxCpApp record);

    List<TWxCpApp> selectByAgentId(String agentId);

    List<TWxCpApp> selectAll();

    List<TWxCpApp> selectByAppName(String appName);
}