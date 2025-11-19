package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TTemplateData;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;
@Mapper
@Component
public interface TTemplateDataMapper {
    int deleteByPrimaryKey(String id);

    int insert(TTemplateData record);

    int insertSelective(TTemplateData record);

    TTemplateData selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TTemplateData record);

    int updateByPrimaryKey(TTemplateData record);

    List<TTemplateData> selectByMsgTypeAndMsgId(@Param("msgType") int msgType, @Param("msgId") String msgId);

    List<TTemplateData> selectByMsgId(@Param("msgId") String msgId);

    int deleteByMsgTypeAndMsgId(@Param("msgType") int msgType, @Param("msgId") String msgId);
}