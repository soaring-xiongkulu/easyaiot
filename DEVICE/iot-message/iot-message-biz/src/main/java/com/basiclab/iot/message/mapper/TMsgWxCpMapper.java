package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TMsgWxCp;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TMsgWxCpMapper {
    int deleteByPrimaryKey(String id);

    int insert(TMsgWxCp record);

    int insertSelective(TMsgWxCp record);

    TMsgWxCp selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TMsgWxCp record);

    int updateByPrimaryKey(TMsgWxCp record);

    List<TMsgWxCp> selectByMsgTypeAndMsgName(@Param("msgType") int msgType, @Param("msgName") String msgName);

    int updateByMsgTypeAndMsgName(TMsgWxCp tMsgWxCp);

    List<TMsgWxCp> selectByMsgType(int msgType);

    int deleteByMsgTypeAndName(@Param("msgType") int msgType, @Param("msgName") String msgName);
}