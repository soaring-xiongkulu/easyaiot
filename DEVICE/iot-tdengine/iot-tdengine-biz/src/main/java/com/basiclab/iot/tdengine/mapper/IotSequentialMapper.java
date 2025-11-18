package com.basiclab.iot.tdengine.mapper;

import com.basiclab.iot.tdengine.domain.IotSequential;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * IotSequentialMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface IotSequentialMapper {

    List<IotSequential> getList(IotSequential iotSequential);

    IotSequential selectByTime(String startTime);

    int save(IotSequential iotSequential);

}
