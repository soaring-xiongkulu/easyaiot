package com.basiclab.iot.device.service.device.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.util.StrUtil;
import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.device.constant.FunctionTypeConstant;
import com.basiclab.iot.device.constant.TdengineConstant;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.device.domain.device.vo.TDDeviceDataResp;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.device.DeviceThingModelService;
import com.basiclab.iot.device.service.product.ProductPropertiesService;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.sink.util.IotSinkRedisKeyConstants;
import com.basiclab.iot.tdengine.RemoteTdEngineService;
import com.basiclab.iot.tdengine.constant.SuperTableTypeConstant;
import com.basiclab.iot.tdengine.domain.DeviceData;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataRequest;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.compress.utils.Lists;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * DeviceThingModelServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Service
public class DeviceThingModelServiceImpl implements DeviceThingModelService {

    @Resource
    private RemoteTdEngineService tdEngineService;
    @Resource
    private ProductPropertiesService productPropertiesService;
    @Resource
    private DeviceService deviceService;
    @Resource
    private ProductService productService;
    @Resource
    private RedisService redisService;

    //设备详情-运行状态
    @Override
    public List<TDDeviceDataResp> getDeviceThingModels(Long id, String name) {
        //先查产品物模型
        Device device = deviceService.selectDeviceById(id);
        if (device == null) {
            return Lists.newArrayList();
        }
        Product product = productService.selectByProductIdentification(device.getProductIdentification());
        if (product == null) {
            return Lists.newArrayList();
        }
        ProductProperties productProperties = new ProductProperties();
        productProperties.setTemplateIdentification(product.getTemplateIdentification());
        productProperties.setProductIdentification(product.getProductIdentification());
        // 仅搜索时按键/名称过滤；未传 name 时不要把 null 写进条件对象
        if (StringUtils.hasText(name)) {
            productProperties.setPropertyCode(name);
            productProperties.setPropertyName(name);
        }
        List<ProductProperties> productPropertiesList = productPropertiesService.selectProductPropertiesList(productProperties);
        if (productPropertiesList.isEmpty()) {
            return Lists.newArrayList();
        }
        List<TDDeviceDataResp> result = BeanUtil.copyToList(productPropertiesList, TDDeviceDataResp.class);
        List<String> propertyCode = result.stream().map(TDDeviceDataResp::getPropertyCode).collect(Collectors.toList());

        JSONObject params = null;
        long ts = 0L;

        // 1) 优先从 TDengine 取最近有效属性上报（整包 params/data JSON）
        TDDeviceDataRequest request = new TDDeviceDataRequest();
        request.setDeviceIdentification(device.getDeviceIdentification());
        request.setIdentifierList(propertyCode);
        request.setFunctionType(FunctionTypeConstant.PROPERTIES);
        request.setTdDatabaseName(TdengineConstant.IOT_DEVICE);
        request.setTdSuperTableName(SuperTableTypeConstant.PROPERTY_UPSTREAM_REPORT);
        try {
            R<List<DeviceData>> lastRowsResp = tdEngineService.getLastRowsListByIdentifier(request);
            if (lastRowsResp != null && lastRowsResp.isSuccess() && !CollectionUtils.isEmpty(lastRowsResp.getData())) {
                for (DeviceData row : lastRowsResp.getData()) {
                    JSONObject parsed = parseParams(row.getDataValue());
                    if (isUsableParams(parsed, propertyCode)) {
                        params = parsed;
                        ts = row.getLastUpdateTime();
                        break;
                    }
                }
            } else if (lastRowsResp != null && !lastRowsResp.isSuccess()) {
                log.warn("查询设备运行状态 TDengine 失败, deviceId={}, msg={}", id, lastRowsResp.getMsg());
            }
        } catch (Exception e) {
            log.warn("查询设备运行状态 TDengine 异常, deviceId={}: {}", id, e.getMessage());
        }

        // 2) TDengine 不可用或最新行无有效 params 时，回退 PostgreSQL 设备影子（上行时已写入）
        if (params == null) {
            ShadowSnapshot shadow = loadShadowParams(device);
            if (shadow != null && isUsableParams(shadow.params, propertyCode)) {
                params = shadow.params;
                ts = shadow.ts;
            }
        }

        if (params != null) {
            applyParams(result, params, propertyCode, ts);
            result.sort(Comparator.comparingLong(TDDeviceDataResp::getTs).reversed());
        }

        // 3) 仍有缺失时，使用 Sink 维护的最新属性缓存（工业协议轮询）
        fillMissingValuesFromRedis(id, result);
        applyPointDisplayConfig(result, device.getExtension());
        return result;
    }

    /**
     * 将设备协议点位中的显示配置补充到运行状态响应。
     * propertyCode 是稳定的物模型绑定键，identifier 只作为用户可维护的点位名称。
     */
    static void applyPointDisplayConfig(List<TDDeviceDataResp> result, String extensionText) {
        if (CollectionUtils.isEmpty(result) || StrUtil.isBlank(extensionText)) {
            return;
        }
        try {
            JSONObject root = JSON.parseObject(extensionText);
            JSONObject protocolConfig = root == null ? null : root.getJSONObject("protocolConfig");
            com.alibaba.fastjson2.JSONArray points = protocolConfig == null
                    ? null : protocolConfig.getJSONArray("points");
            if (points == null || points.isEmpty()) {
                return;
            }
            Map<String, JSONObject> pointMap = new HashMap<>();
            for (int i = 0; i < points.size(); i++) {
                JSONObject point = points.getJSONObject(i);
                if (point == null) {
                    continue;
                }
                String propertyCode = StrUtil.blankToDefault(
                        point.getString("propertyCode"), point.getString("identifier"));
                if (StrUtil.isNotBlank(propertyCode)) {
                    pointMap.put(propertyCode, point);
                }
            }
            for (TDDeviceDataResp item : result) {
                JSONObject point = pointMap.get(item.getPropertyCode());
                if (point == null) {
                    continue;
                }
                String pointName = StrUtil.trim(point.getString("identifier"));
                // 旧配置 identifier 与 propertyCode 相同，此时继续展示更友好的物模型名称。
                if (StrUtil.isNotBlank(pointName) && !pointName.equals(item.getPropertyCode())) {
                    item.setPointName(pointName);
                }
                Integer decimalPlaces = point.getInteger("decimalPlaces");
                if (decimalPlaces != null) {
                    item.setDecimalPlaces(Math.max(0, Math.min(10, decimalPlaces)));
                }
            }
        } catch (Exception e) {
            log.debug("解析点位显示配置失败: {}", e.getMessage());
        }
    }

    private void applyParams(List<TDDeviceDataResp> result, JSONObject params,
                             List<String> propertyCode, long ts) {
        Object rawObj = params.get("_raw");
        JSONObject rawMap = rawObj instanceof JSONObject ? (JSONObject) rawObj
                : (rawObj instanceof Map ? new JSONObject((Map<String, Object>) rawObj) : null);
        for (TDDeviceDataResp resp : result) {
            if (params.containsKey(resp.getPropertyCode())) {
                Object value = params.get(resp.getPropertyCode());
                resp.setDataValue(value == null ? null : String.valueOf(value));
                if (ts > 0) {
                    resp.setTs(ts);
                }
            } else if (params.size() == 1 && propertyCode.size() == 1) {
                Object value = params.values().iterator().next();
                resp.setDataValue(value == null ? null : String.valueOf(value));
                if (ts > 0) {
                    resp.setTs(ts);
                }
            }
            if (rawMap != null && rawMap.containsKey(resp.getPropertyCode())) {
                Object raw = rawMap.get(resp.getPropertyCode());
                resp.setRawData(raw == null ? null : String.valueOf(raw));
            }
        }
    }

    /**
     * TDengine / 影子不可用或尚未写入时，使用 Sink 维护的最新属性缓存。
     */
    @SuppressWarnings("unchecked")
    private void fillMissingValuesFromRedis(Long deviceId, List<TDDeviceDataResp> result) {
        if (CollectionUtils.isEmpty(result)) {
            return;
        }
        String redisKey = IotSinkRedisKeyConstants.buildDeviceDataKey(deviceId);
        String extensionJson = redisService.getCacheMapValue(
                redisKey, IotSinkRedisKeyConstants.DEVICE_DATA_FIELD_EXTENSION);
        if (StrUtil.isBlank(extensionJson)) {
            return;
        }

        Map<String, Object> extension;
        try {
            extension = JSON.parseObject(extensionJson, Map.class);
        } catch (Exception e) {
            log.warn("[fillMissingValuesFromRedis][解析设备属性缓存失败，deviceId: {}]", deviceId, e);
            return;
        }
        if (extension == null) {
            return;
        }
        Object propertiesValue = extension.get("properties");
        if (!(propertiesValue instanceof Map)) {
            return;
        }
        Map<String, Object> properties = (Map<String, Object>) propertiesValue;
        Object rawObj = properties.get("_raw");
        Map<String, Object> rawMap = rawObj instanceof Map ? (Map<String, Object>) rawObj : null;
        long timestamp = toEpochMilli(properties.get("timestamp"));
        boolean filled = false;
        for (TDDeviceDataResp item : result) {
            if (item.getDataValue() == null && properties.containsKey(item.getPropertyCode())) {
                Object value = properties.get(item.getPropertyCode());
                if (value != null) {
                    item.setDataValue(String.valueOf(value));
                    // 缓存无有效时间戳时不要写成 0，避免前端时间在有效值/-- 之间闪烁
                    if (timestamp > 0) {
                        item.setTs(timestamp);
                    } else if (item.getTs() <= 0) {
                        item.setTs(System.currentTimeMillis());
                    }
                    filled = true;
                }
            }
            if (item.getRawData() == null && rawMap != null && rawMap.containsKey(item.getPropertyCode())) {
                Object raw = rawMap.get(item.getPropertyCode());
                if (raw != null) {
                    item.setRawData(String.valueOf(raw));
                }
            }
        }
        if (filled) {
            result.sort(Comparator.comparingLong(TDDeviceDataResp::getTs).reversed());
        }
    }

    private boolean isUsableParams(JSONObject params, List<String> propertyCodes) {
        if (params == null || params.isEmpty()) {
            return false;
        }
        // 仅有兼容包装键时不算有效运行态
        if (params.size() == 1 && (params.containsKey("_raw") || params.containsKey("_value"))) {
            return propertyCodes != null && propertyCodes.size() == 1;
        }
        if (CollectionUtils.isEmpty(propertyCodes)) {
            return true;
        }
        for (String code : propertyCodes) {
            if (params.containsKey(code)) {
                return true;
            }
        }
        return params.size() == 1 && propertyCodes.size() == 1;
    }

    private ShadowSnapshot loadShadowParams(Device device) {
        if (device == null || !StringUtils.hasText(device.getExtension())) {
            return null;
        }
        try {
            JSONObject extension = JSON.parseObject(device.getExtension());
            if (extension == null) {
                return null;
            }
            Object shadowObj = extension.get("shadow");
            JSONObject params = null;
            if (shadowObj instanceof JSONObject) {
                params = (JSONObject) shadowObj;
            } else if (shadowObj instanceof Map) {
                params = new JSONObject((Map<String, Object>) shadowObj);
            } else if (shadowObj instanceof String && StringUtils.hasText((String) shadowObj)) {
                params = parseParams((String) shadowObj);
            }
            if (params == null || params.isEmpty()) {
                return null;
            }
            long ts = 0L;
            Object updateTime = extension.get("shadowUpdateTime");
            if (updateTime != null) {
                ts = toEpochMilli(updateTime);
            }
            if (ts <= 0 && device.getUpdateTime() != null) {
                ts = toEpochMilli(device.getUpdateTime());
            }
            if (ts <= 0 && device.getLastOnlineTime() != null) {
                ts = device.getLastOnlineTime().atZone(ZoneId.systemDefault()).toInstant().toEpochMilli();
            }
            return new ShadowSnapshot(params, ts);
        } catch (Exception e) {
            log.debug("解析设备影子失败, deviceId={}: {}", device.getId(), e.getMessage());
            return null;
        }
    }

    private long toEpochMilli(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        if (value instanceof LocalDateTime) {
            return ((LocalDateTime) value).atZone(ZoneId.systemDefault()).toInstant().toEpochMilli();
        }
        String text = String.valueOf(value).trim();
        if (!StringUtils.hasText(text)) {
            return 0L;
        }
        try {
            return Long.parseLong(text);
        } catch (NumberFormatException ignored) {
            // continue
        }
        try {
            return LocalDateTime.parse(text.replace(" ", "T").substring(0, Math.min(text.length(), 19)))
                    .atZone(ZoneId.systemDefault()).toInstant().toEpochMilli();
        } catch (Exception ignored) {
            return 0L;
        }
    }

    static JSONObject parseParams(String raw) {
        if (!StringUtils.hasText(raw)) {
            return null;
        }
        String text = raw.trim();
        try {
            Object parsed = JSON.parse(text);
            if (parsed instanceof JSONObject) {
                return (JSONObject) parsed;
            }
            // 非对象时包一层，便于单值展示
            JSONObject wrap = new JSONObject();
            wrap.put("_value", parsed);
            return wrap;
        } catch (Exception ignored) {
            // 兼容历史脏数据：TDengine 写入时双引号被吃掉，形如 {temperature:1.2,Vbatt:3.7}
            JSONObject recovered = tryRecoverUnquotedJson(text);
            if (recovered != null) {
                return recovered;
            }
            JSONObject wrap = new JSONObject();
            wrap.put("_raw", text);
            return wrap;
        }
    }

    /**
     * 将 {k:v,k2:v2} 宽松解析为 JSONObject（仅用于运行状态展示兼容）。
     */
    static JSONObject tryRecoverUnquotedJson(String raw) {
        if (!raw.startsWith("{") || !raw.endsWith("}")) {
            return null;
        }
        try {
            String body = raw.substring(1, raw.length() - 1).trim();
            if (!StringUtils.hasText(body)) {
                return new JSONObject();
            }
            JSONObject obj = new JSONObject();
            for (String part : splitTopLevel(body)) {
                int idx = findTopLevelColon(part);
                if (idx <= 0) {
                    continue;
                }
                String key = unquote(part.substring(0, idx).trim());
                String val = part.substring(idx + 1).trim();
                if (StrUtil.isBlank(key)) {
                    continue;
                }
                obj.put(key, parseLooseValue(val));
            }
            return obj.isEmpty() ? null : obj;
        } catch (Exception e) {
            return null;
        }
    }

    /** 仅在对象最外层按逗号分割，避免嵌套 _raw 对象中的同名键覆盖解析值。 */
    private static List<String> splitTopLevel(String body) {
        List<String> parts = new ArrayList<>();
        int start = 0;
        int depth = 0;
        char quote = 0;
        boolean escaped = false;
        for (int i = 0; i < body.length(); i++) {
            char ch = body.charAt(i);
            if (quote != 0) {
                if (escaped) {
                    escaped = false;
                } else if (ch == '\\') {
                    escaped = true;
                } else if (ch == quote) {
                    quote = 0;
                }
                continue;
            }
            if (ch == '\'' || ch == '"') {
                quote = ch;
            } else if (ch == '{' || ch == '[' || ch == '(') {
                depth++;
            } else if (ch == '}' || ch == ']' || ch == ')') {
                depth = Math.max(0, depth - 1);
            } else if (ch == ',' && depth == 0) {
                parts.add(body.substring(start, i).trim());
                start = i + 1;
            }
        }
        parts.add(body.substring(start).trim());
        return parts;
    }

    private static int findTopLevelColon(String part) {
        int depth = 0;
        char quote = 0;
        boolean escaped = false;
        for (int i = 0; i < part.length(); i++) {
            char ch = part.charAt(i);
            if (quote != 0) {
                if (escaped) {
                    escaped = false;
                } else if (ch == '\\') {
                    escaped = true;
                } else if (ch == quote) {
                    quote = 0;
                }
                continue;
            }
            if (ch == '\'' || ch == '"') {
                quote = ch;
            } else if (ch == '{' || ch == '[' || ch == '(') {
                depth++;
            } else if (ch == '}' || ch == ']' || ch == ')') {
                depth = Math.max(0, depth - 1);
            } else if (ch == ':' && depth == 0) {
                return i;
            }
        }
        return -1;
    }

    private static Object parseLooseValue(String value) {
        String text = value == null ? "" : value.trim();
        if (text.startsWith("{") && text.endsWith("}")) {
            JSONObject nested = tryRecoverUnquotedJson(text);
            return nested == null ? text : nested;
        }
        try {
            return JSON.parse(text);
        } catch (Exception ignored) {
            return unquote(text);
        }
    }

    private static String unquote(String value) {
        if (value != null && value.length() >= 2) {
            char first = value.charAt(0);
            char last = value.charAt(value.length() - 1);
            if ((first == '"' && last == '"') || (first == '\'' && last == '\'')) {
                return value.substring(1, value.length() - 1);
            }
        }
        return value;
    }

    private static final class ShadowSnapshot {
        private final JSONObject params;
        private final long ts;

        private ShadowSnapshot(JSONObject params, long ts) {
            this.params = params;
            this.ts = ts;
        }
    }

}
