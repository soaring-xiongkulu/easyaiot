package com.basiclab.iot.tdengine.service.impl;

import com.basiclab.iot.tdengine.domain.IotSequential;
import com.basiclab.iot.tdengine.mapper.IotSequentialMapper;
import com.basiclab.iot.tdengine.service.IotSequentialService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class IotSequentialServiceImpl implements IotSequentialService {

    @Autowired
    private IotSequentialMapper iotSequentialMapper;

    public IotSequential selectByTime(String startTime){
        return iotSequentialMapper.selectByTime(startTime);
    }

    public List<IotSequential> getList(IotSequential iotSequential){
        return iotSequentialMapper.getList(iotSequential);
    }

    public int save(IotSequential iotSequential){
        return iotSequentialMapper.save(iotSequential);
    }
}
