package com.basiclab.iot.message.mapper;


import com.basiclab.iot.message.domain.entity.TDingApp;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TDingAppMapper {
    int deleteByPrimaryKey(String id);

    int insert(TDingApp record);

    int insertSelective(TDingApp record);

    TDingApp selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TDingApp record);

    int updateByPrimaryKey(TDingApp record);

    List<TDingApp> selectByAppName(String appName);

    List<TDingApp> selectAll();

    TDingApp selectByAgentId(String agentId);
}