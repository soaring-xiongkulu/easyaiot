package com.basiclab.iot.tdengine.mapper;

import com.basiclab.iot.tdengine.domain.IotSequential;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface IotSequentialMapper {

    List<IotSequential> getList(IotSequential iotSequential);

    IotSequential selectByTime(String startTime);

    int save(IotSequential iotSequential);

}
