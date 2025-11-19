package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TMsgSms;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TMsgSmsMapper {
    int deleteByPrimaryKey(String id);

    int insert(TMsgSms record);

    int insertSelective(TMsgSms record);

    TMsgSms selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TMsgSms record);

    int updateByPrimaryKey(TMsgSms record);

    List<TMsgSms> selectByMsgTypeAndMsgName(@Param("msgType") int msgType, @Param("msgName") String msgName);

    int updateByMsgTypeAndMsgName(TMsgSms tMsgSms);

    List<TMsgSms> selectByMsgType(int msgType);

    int deleteByMsgTypeAndName(@Param("msgType") int msgType, @Param("msgName") String msgName);
}