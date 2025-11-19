package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TMsgDing;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TMsgDingMapper {
    int deleteByPrimaryKey(String id);

    int insert(TMsgDing record);

    int insertSelective(TMsgDing record);

    TMsgDing selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TMsgDing record);

    int updateByPrimaryKey(TMsgDing record);

    List<TMsgDing> selectByMsgTypeAndMsgName(@Param("msgType") int msgType, @Param("msgName") String msgName);

    int updateByMsgTypeAndMsgName(TMsgDing tMsgDing);

    List<TMsgDing> selectByMsgType(int msgType);

    int deleteByMsgTypeAndName(@Param("msgType") int msgType, @Param("msgName") String msgName);
}