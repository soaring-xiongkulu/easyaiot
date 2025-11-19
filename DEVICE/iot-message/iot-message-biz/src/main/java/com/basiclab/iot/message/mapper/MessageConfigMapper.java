package com.basiclab.iot.message.mapper;

import com.basiclab.iot.message.domain.entity.MessageConfig;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 消息配置mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Component
@Mapper
public interface MessageConfigMapper {
     int add(MessageConfig messageConfig);

     int update(MessageConfig messageConfig);

     int delete(String id);

     List<MessageConfig> selectList(@Param("messageConfig") MessageConfig messageConfig);

     MessageConfig selectById(String id);

     MessageConfig selectByMsgType(int msgType);

}
