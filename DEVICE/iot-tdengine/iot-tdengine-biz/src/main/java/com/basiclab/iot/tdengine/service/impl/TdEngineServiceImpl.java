package com.basiclab.iot.tdengine.service.impl;

import com.basiclab.iot.device.constant.FunctionTypeConstant;
import com.basiclab.iot.device.constant.TdengineConstant;
import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import com.basiclab.iot.tdengine.domain.DeviceData;
import com.basiclab.iot.tdengine.domain.Fields;
import com.basiclab.iot.tdengine.domain.SelectDto;
import com.basiclab.iot.tdengine.domain.SuperTableDescribeVO;
import com.basiclab.iot.tdengine.domain.model.SuperTableDTO;
import com.basiclab.iot.tdengine.domain.model.TableDTO;
import com.basiclab.iot.tdengine.domain.model.TagsSelectDTO;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataHistoryRequest;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataRequest;
import com.basiclab.iot.tdengine.mapper.TdEngineMapper;
import com.basiclab.iot.tdengine.service.TdEngineService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.*;
import java.util.stream.Collectors;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
@Transactional(isolation = Isolation.DEFAULT, propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
public class TdEngineServiceImpl implements TdEngineService {

    @Resource
    private TdEngineMapper tdengineMapper;

    @Override
    public void createDatabase(String dataBaseName) {
        tdengineMapper.createDatabase(dataBaseName);
    }

    @Override
    public void createSuperTable(String dataBaseName, String superTableName) {
        tdengineMapper.createSuperTable(dataBaseName, superTableName);
    }

    @Override
    public void createSuperTableAndColumn(SuperTableDTO superTableDTO) {
        tdengineMapper.createSuperTableAndColumn(superTableDTO);
    }

    @Override
    public void createSubTable(TableDTO tableDTO) {
        tdengineMapper.createSubTable(tableDTO);
    }

    @Override
    public void dropSuperTable(String dataBaseName, String superTableName) {
        tdengineMapper.dropSuperTable(dataBaseName, superTableName);
    }

    @Override
    public void alterSuperTableColumn(String dataBaseName, String superTableName, Fields fields) {
        tdengineMapper.alterSuperTableColumn(dataBaseName, superTableName, fields);
    }

    @Override
    public void dropSuperTableColumn(String dataBaseName, String superTableName, Fields fields) {
        tdengineMapper.dropSuperTableColumn(dataBaseName, superTableName, fields);
    }

    @Override
    public List<SuperTableDescribeVO> describeSuperOrSubTable(String dataBaseName, String tableName) {
        try {
            return tdengineMapper.describeSuperOrSubTable(dataBaseName, tableName);
        } catch (Exception e) {
            log.warn("Error describing super or sub table. Database: {}, Table: {}, Error: {}", dataBaseName, tableName, e.getMessage());
            return Collections.emptyList();
        }
    }

    @Override
    public void alterSuperTableTag(String dataBaseName, String superTableName, Fields fields) {
        tdengineMapper.alterSuperTableTag(dataBaseName, superTableName, fields);
    }

    @Override
    public void dropSuperTableTag(String dataBaseName, String superTableName, Fields fields) {
        tdengineMapper.dropSuperTableTag(dataBaseName, superTableName, fields);
    }

    @Override
    public void alterSuperTableTagRename(String dataBaseName, String superTableName, String oldName, String newName) {
        tdengineMapper.alterSuperTableTagRename(dataBaseName, superTableName, oldName, newName);
    }

    @Override
    public void insertTableData(TableDTO tableDTO) {
        tdengineMapper.insertTableData(tableDTO);
    }

    @Override
    public Map<String, Map<String, Object>> getLastDataByTags(TagsSelectDTO tagsSelectDTO) {
        List<Map<String, Object>> maps = tdengineMapper.getLastDataByTags(tagsSelectDTO);
        Map<String, Map<String, Object>> objectHashMap = new HashMap<>();

        for (Map<String, Object> map : maps) {
            Optional.ofNullable(map.get(tagsSelectDTO.getTagsName()))
                    .map(Object::toString)
                    .ifPresent(key -> objectHashMap.put(key, map));
        }
        return objectHashMap;
    }


    @Override
    public List<Map<String, Object>> getDataInRangeOrLastRecord(String dataBaseName, String tableName, Long startTime, Long endTime) {
        return tdengineMapper.getDataInRangeOrLastRecord(dataBaseName, tableName, startTime, endTime);
    }


    @Override
    public List<Map<String, Object>> selectByTimesTamp(SelectDto selectDto) throws Exception {
        List<Map<String, Object>> maps = tdengineMapper.selectByTimestamp(selectDto);
        for (Map<String, Object> map : maps) {
            Map<String, Object> filterMap = map.entrySet()
                    .stream()
                    .filter(entry -> entry.getValue() != null)
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
        }
        return maps;
    }


    /**
     * @param selectDto
     * @return
     */
    @Override
    public List<Map<String, Object>> getLastData(SelectDto selectDto) throws Exception {
        List<Map<String, Object>> maps = this.tdengineMapper.getLastData(selectDto);
//        for (Map<String, Object> map : maps) {
//            Map<String, Object> filterMap = map.entrySet()
//                    .stream()
//                    .filter(entry -> entry.getValue() != null)
//                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
//        }
        return maps;
    }

    @Override
    public List<DeviceData> getLastRowsListByIdentifier(TDDeviceDataRequest tdDeviceDataRequest) {
        List<DeviceData> list = new ArrayList<>();
        try{
            list = tdengineMapper.getLastRowsListByIdentifier(tdDeviceDataRequest);
        }catch (Exception e){
            log.error("getLastRowsListByIdentifier error: {}",e.getMessage());
        }
        return list;
    }

    @Override
    public List<TDDeviceDataResp> deviceInfoHistoryPage(TDDeviceDataHistoryRequest request) {
        request.setFunctionType(FunctionTypeConstant.PROPERTIES);
        request.setTdDatabaseName(TdengineConstant.IOT_DEVICE);
        request.setTdSuperTableName(TdengineConstant.DEVICE_DATA);
        try {
            return tdengineMapper.getDeviceHistory(request);
        } catch (Exception e) {
            log.error("查询运行时属性异常：" + e.getMessage());
        }
        return null;
    }

}
