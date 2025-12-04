package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TMsgFeishu;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TMsgFeishuMapper {
    int deleteByPrimaryKey(String id);

    int insert(TMsgFeishu record);

    int insertSelective(TMsgFeishu record);

    TMsgFeishu selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TMsgFeishu record);

    int updateByPrimaryKey(TMsgFeishu record);

    List<TMsgFeishu> selectByMsgTypeAndMsgName(@Param("msgType") int msgType, @Param("msgName") String msgName);

    int updateByMsgTypeAndMsgName(TMsgFeishu tMsgFeishu);

    List<TMsgFeishu> selectByMsgType(int msgType);
}

