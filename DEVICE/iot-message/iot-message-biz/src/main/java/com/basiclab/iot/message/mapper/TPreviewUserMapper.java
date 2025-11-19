package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.TPreviewUser;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@Mapper
public interface TPreviewUserMapper {
    int add(TPreviewUser tPreviewUser);

    int update(TPreviewUser tPreviewUser);

    int delete(String id);

    List<TPreviewUser> selectList(@Param("tPreviewUser") TPreviewUser tPreviewUser);

    List<TPreviewUser> queryByMsgType(int msgType);

    Integer getUserCount(@Param("msgType") int msgType,@Param("previewUser") String previewUser);

    List<TPreviewUser> queryByIds(@Param("ids") List<String> ids);

    List<String> queryPreviewUsers(@Param("ids") List<String> ids);
}
