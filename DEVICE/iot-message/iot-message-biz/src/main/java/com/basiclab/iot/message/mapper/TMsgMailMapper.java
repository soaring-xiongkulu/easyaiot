package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TMsgMail;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TMsgMailMapper {
    int deleteByPrimaryKey(String id);

    int insert(TMsgMail record);

    int insertSelective(TMsgMail record);

    TMsgMail selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TMsgMail record);

    int updateByPrimaryKey(TMsgMail record);

    List<TMsgMail> selectByMsgTypeAndMsgName(@Param("msgType") int msgType, @Param("msgName") String msgName);

    int updateByMsgTypeAndMsgName(TMsgMail tMsgMail);

    List<TMsgMail> selectByMsgType(int msgType);

    int deleteByMsgTypeAndName(@Param("msgType") int msgType, @Param("msgName") String msgName);
}