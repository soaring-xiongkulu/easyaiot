package com.basiclab.iot.device.service.product_properties;

import com.basiclab.iot.device.dal.dataobject.product.DeviceData;
import com.basiclab.iot.device.dal.dataobject.product.TDDeviceDataRequest;
import com.basiclab.iot.device.dal.taos.product.TdEngineMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;

/**
 * @author Basiclab
 */
@Service
@Slf4j
@Transactional(isolation = Isolation.DEFAULT, propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public class TdEngineServiceImpl implements TdEngineService {

    @Resource
    private TdEngineMapper tdengineMapper;

    @Override
    public List<DeviceData> getLastRowsListByIdentifier(TDDeviceDataRequest tdDeviceDataRequest) {
        List<DeviceData> list = new ArrayList<>();
        try {
            list = tdengineMapper.getLastRowsListByIdentifier(tdDeviceDataRequest);
        } catch (Exception e) {
            log.error("getLastRowsListByIdentifier error: {}", e.getMessage());
        }
        return list;
    }

}
