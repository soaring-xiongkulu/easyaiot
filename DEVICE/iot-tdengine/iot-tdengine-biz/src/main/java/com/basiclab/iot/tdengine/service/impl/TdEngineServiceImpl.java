package com.basiclab.iot.tdengine.service.impl;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.device.constant.FunctionTypeConstant;
import com.basiclab.iot.device.constant.TdengineConstant;
import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import com.basiclab.iot.tdengine.constant.SuperTableTypeConstant;
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

import javax.annotation.Resource;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class TdEngineServiceImpl implements TdEngineService {

    private static final Set<String> HISTORY_METADATA_KEYS = new HashSet<>(Arrays.asList(
            "deviceId", "device_id", "serverId", "server_id", "serviceId", "service_id",
            "requestId", "request_id", "method", "topic", "tenantId", "tenant_id",
            "productIdentification", "product_identification", "code", "msg", "id"
    ));

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
        try {
            // deviceIdentification 用作超级表 TAG，保持原始设备标识（勿做子表名清洗）
            if (tdDeviceDataRequest.getTdSuperTableName() == null
                    || "device_data".equals(tdDeviceDataRequest.getTdSuperTableName())) {
                tdDeviceDataRequest.setTdSuperTableName(SuperTableTypeConstant.PROPERTY_UPSTREAM_REPORT);
            }
            list = tdengineMapper.getLastRowsListByIdentifier(tdDeviceDataRequest);
        } catch (Exception e) {
            log.error("getLastRowsListByIdentifier error: {}", e.getMessage());
        }
        return list;
    }

    @Override
    public List<TDDeviceDataResp> deviceInfoHistoryPage(TDDeviceDataHistoryRequest request) {
        request.setFunctionType(FunctionTypeConstant.PROPERTIES);
        request.setTdDatabaseName(TdengineConstant.IOT_DEVICE);
        // 按超级表 TAG(device_identification) 查询，与 sink 写入 TAG 一致
        request.setTdSuperTableName(SuperTableTypeConstant.PROPERTY_UPSTREAM_REPORT);
        try {
            List<TDDeviceDataResp> rows = tdengineMapper.getDeviceHistory(request);
            return extractHistoryPropertyValues(rows, request.getIdentifier());
        } catch (Exception e) {
            log.error("查询运行时属性异常：" + e.getMessage());
        }
        return Collections.emptyList();
    }

    /**
     * 历史表存的是整包 params JSON，按 identifier 提取单属性值与工业协议原始报文。
     */
    private List<TDDeviceDataResp> extractHistoryPropertyValues(List<TDDeviceDataResp> rows, String identifier) {
        if (rows == null || rows.isEmpty()) {
            return Collections.emptyList();
        }
        String propertyCode = StrUtil.trimToEmpty(identifier);
        List<TDDeviceDataResp> result = new ArrayList<>(rows.size());
        for (TDDeviceDataResp row : rows) {
            if (row == null) {
                continue;
            }
            String raw = row.getDataValue();
            if (StrUtil.isBlank(raw)) {
                continue;
            }
            String text = raw.trim();
            if (!text.startsWith("{") && !text.startsWith("[")) {
                if (StrUtil.isNotBlank(propertyCode)) {
                    row.setPropertyCode(propertyCode);
                }
                result.add(row);
                continue;
            }
            JSONObject params = null;
            try {
                params = JSONUtil.parseObj(text);
            } catch (Exception ignored) {
                // 设备上报可能是 {key:value} 非标准 JSON（键未加引号）
            }
            Object value = params != null ? resolveHistoryValue(params, propertyCode) : null;
            if (value == null && StrUtil.isNotBlank(propertyCode)) {
                value = extractLoosePropertyValue(text, propertyCode);
            }
            if (value == null && StrUtil.isNotBlank(propertyCode)) {
                // 该上报包不含目标属性，跳过
                continue;
            }
            if (value != null) {
                row.setDataValue(formatHistoryValue(value));
            }
            if (StrUtil.isNotBlank(propertyCode)) {
                row.setPropertyCode(propertyCode);
                if (params != null) {
                    Object rawPayload = resolveHistoryRaw(params, propertyCode);
                    if (rawPayload != null) {
                        row.setRawData(String.valueOf(rawPayload));
                    }
                }
            }
            result.add(row);
        }
        return result;
    }

    private Object resolveHistoryValue(JSONObject params, String propertyCode) {
        JSONObject payload = normalizeHistoryParams(params);
        if (payload == null || payload.isEmpty()) {
            return null;
        }
        if (StrUtil.isNotBlank(propertyCode)) {
            Object direct = readPropertyValue(payload, propertyCode);
            if (direct != null) {
                return direct;
            }
            Object nested = payload.get("properties");
            if (nested instanceof JSONObject) {
                direct = readPropertyValue((JSONObject) nested, propertyCode);
                if (direct != null) {
                    return direct;
                }
            }
            nested = payload.get("data");
            if (nested instanceof JSONObject) {
                direct = readPropertyValue((JSONObject) nested, propertyCode);
                if (direct != null) {
                    return direct;
                }
            }
            if (payload.get("_value") != null) {
                return payload.get("_value");
            }
            return null;
        }
        if (payload.get("_value") != null) {
            return payload.get("_value");
        }
        List<Map.Entry<String, Object>> candidates = payload.entrySet().stream()
                .filter(entry -> entry.getKey() != null
                        && !entry.getKey().startsWith("_")
                        && !isHistoryMetadataKey(entry.getKey()))
                .collect(Collectors.toList());
        if (candidates.size() == 1) {
            return candidates.get(0).getValue();
        }
        return null;
    }

    private JSONObject normalizeHistoryParams(JSONObject params) {
        if (params == null) {
            return null;
        }
        JSONObject current = params;
        Object innerParams = current.get("params");
        if (innerParams instanceof JSONObject) {
            current = (JSONObject) innerParams;
        } else if (innerParams instanceof Map) {
            current = JSONUtil.parseObj(JSONUtil.toJsonStr(innerParams));
        }
        Object properties = current.get("properties");
        if (properties instanceof JSONObject) {
            return (JSONObject) properties;
        }
        if (properties instanceof Map) {
            return JSONUtil.parseObj(JSONUtil.toJsonStr(properties));
        }
        return current;
    }

    private Object readPropertyValue(JSONObject payload, String propertyCode) {
        if (payload == null || StrUtil.isBlank(propertyCode) || !payload.containsKey(propertyCode)) {
            return null;
        }
        return payload.get(propertyCode);
    }

    private boolean isHistoryMetadataKey(String key) {
        return HISTORY_METADATA_KEYS.contains(key);
    }

    private String formatHistoryValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Map || value instanceof JSONObject) {
            return JSONUtil.toJsonStr(value);
        }
        return String.valueOf(value);
    }

    /**
     * 从非标准 {key:value} 文本中提取属性值，例如 {deviceId:1,Vbatt:3.39,...}。
     */
    private Object extractLoosePropertyValue(String text, String propertyCode) {
        if (StrUtil.isBlank(text) || StrUtil.isBlank(propertyCode)) {
            return null;
        }
        Pattern pattern = Pattern.compile("(?:^|[,{\\s])" + Pattern.quote(propertyCode) + "\\s*:\\s*([^,}]+)");
        Matcher matcher = pattern.matcher(text);
        if (matcher.find()) {
            return matcher.group(1).trim();
        }
        return null;
    }

    private Object resolveHistoryRaw(JSONObject params, String propertyCode) {
        JSONObject payload = normalizeHistoryParams(params);
        if (payload == null || StrUtil.isBlank(propertyCode)) {
            return null;
        }
        Object rawObj = params.get("_raw");
        if (rawObj == null) {
            rawObj = payload.get("_raw");
        }
        if (rawObj instanceof JSONObject) {
            return ((JSONObject) rawObj).get(propertyCode);
        }
        if (rawObj instanceof Map) {
            return ((Map<?, ?>) rawObj).get(propertyCode);
        }
        return null;
    }

    @Override
    public List<Map<String, Object>> queryDeviceTimeSeriesData(com.basiclab.iot.tdengine.domain.query.DeviceTimeSeriesQueryRequest request) {
        try {
            if (request.getTdDatabaseName() == null) {
                request.setTdDatabaseName("iot_device");
            }
            if (request.getSuperTableName() == null) {
                String type = request.getSuperTableType();
                if (type != null && !type.startsWith("st_")) {
                    // 允许传枚举名 PROPERTY_UPSTREAM_REPORT
                    request.setSuperTableName("st_" + type.toLowerCase());
                } else {
                    request.setSuperTableName(type);
                }
            }
            // deviceIdentification 为超级表 TAG，保持原始值
            return tdengineMapper.queryDeviceTimeSeriesData(request);
        } catch (Exception e) {
            log.error("查询设备时序数据异常：deviceIdentification={}, superTableType={}, error={}",
                    request.getDeviceIdentification(), request.getSuperTableType(), e.getMessage(), e);
            return Collections.emptyList();
        }
    }

}
