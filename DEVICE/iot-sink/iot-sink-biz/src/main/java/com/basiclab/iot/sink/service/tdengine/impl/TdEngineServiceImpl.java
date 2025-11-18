package com.basiclab.iot.sink.service.tdengine.impl;

import com.basiclab.iot.sink.dal.mapper.TdEngineMapper;
import com.basiclab.iot.sink.service.tdengine.TdEngineService;
import com.basiclab.iot.tdengine.domain.model.TableDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;

/**
 * TdEngineServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Service
@Transactional(isolation = Isolation.DEFAULT, propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public class TdEngineServiceImpl implements TdEngineService {

    @Resource
    private TdEngineMapper tdEngineMapper;

    @Override
    public void insertTableData(TableDTO tableDTO) {
        try {
            tdEngineMapper.insertTableData(tableDTO);
            log.debug("[insertTableData][TDEngine数据插入成功，tableName: {}]", tableDTO.getTableName());
        } catch (Exception e) {
            log.error("[insertTableData][TDEngine数据插入失败，tableName: {}]", tableDTO.getTableName(), e);
            throw e;
        }
    }
}

