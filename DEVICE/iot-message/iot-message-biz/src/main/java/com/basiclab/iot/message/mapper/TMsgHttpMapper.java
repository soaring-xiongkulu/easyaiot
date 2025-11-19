package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TMsgHttp;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TMsgHttpMapper {
    int deleteByPrimaryKey(String id);

    int insert(TMsgHttp record);

    int insertSelective(TMsgHttp record);

    TMsgHttp selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TMsgHttp record);

    int updateByPrimaryKey(TMsgHttp record);

    List<TMsgHttp> selectByMsgTypeAndMsgName(@Param("msgType") int msgType, @Param("msgName") String msgName);

    int updateByMsgTypeAndMsgName(TMsgHttp tMsgHttp);

    List<TMsgHttp> selectByMsgType(int msgType);

    int deleteByMsgTypeAndName(@Param("msgType") int msgType, @Param("msgName") String msgName);
}