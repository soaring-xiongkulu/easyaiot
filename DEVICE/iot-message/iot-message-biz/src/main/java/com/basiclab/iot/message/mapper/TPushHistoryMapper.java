package com.basiclab.iot.message.mapper;


import com.basiclab.iot.message.domain.entity.TPushHistory;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Mapper
@Component
public interface TPushHistoryMapper {
    int deleteByPrimaryKey(String id);

    int insert(TPushHistory record);

    int insertSelective(TPushHistory record);

    TPushHistory selectByPrimaryKey(String id);

    int updateByPrimaryKeySelective(TPushHistory record);

    int updateByPrimaryKey(TPushHistory record);

    List<TPushHistory> selectByMsgType(@Param("msgType") Integer msgType,@Param("msgName")String msgName);
}