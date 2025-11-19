package com.basiclab.iot.message.mapper;


import com.basiclab.iot.message.domain.entity.TWxMpUser;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.stereotype.Component;

@Component
@Mapper
public interface TWxMpUserMapper {
    int deleteByPrimaryKey(String openId);

    int insert(TWxMpUser record);

    int insertSelective(TWxMpUser record);

    TWxMpUser selectByPrimaryKey(String openId);

    int updateByPrimaryKeySelective(TWxMpUser record);

    int updateByPrimaryKey(TWxMpUser record);

    int deleteAll();
}