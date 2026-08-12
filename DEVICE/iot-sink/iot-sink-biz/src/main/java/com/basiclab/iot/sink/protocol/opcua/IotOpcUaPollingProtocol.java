package com.basiclab.iot.sink.protocol.opcua;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import com.basiclab.iot.sink.dal.mapper.DeviceMapper;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.protocol.polling.AbstractIndustrialPollingProtocol;
import com.basiclab.iot.sink.protocol.polling.IndustrialDeviceConfig;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.milo.opcua.sdk.client.OpcUaClient;
import org.eclipse.milo.opcua.sdk.client.identity.AnonymousProvider;
import org.eclipse.milo.opcua.sdk.client.identity.UsernameProvider;
import org.eclipse.milo.opcua.stack.core.security.SecurityPolicy;
import org.eclipse.milo.opcua.stack.core.types.builtin.ByteString;
import org.eclipse.milo.opcua.stack.core.types.builtin.DataValue;
import org.eclipse.milo.opcua.stack.core.types.builtin.NodeId;
import org.eclipse.milo.opcua.stack.core.types.builtin.StatusCode;
import org.eclipse.milo.opcua.stack.core.types.builtin.Variant;
import org.eclipse.milo.opcua.stack.core.types.enumerated.TimestampsToReturn;

import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

@Slf4j
public class IotOpcUaPollingProtocol extends AbstractIndustrialPollingProtocol {

    public static final String PROTOCOL_TYPE = "OPCUA";

    private final Map<String, OpcUaClient> clients = new ConcurrentHashMap<>();
    private final Map<String, Object> clientLocks = new ConcurrentHashMap<>();

    public IotOpcUaPollingProtocol(IotGatewayProperties.PollingProtocolProperties properties,
                                   DeviceMapper deviceMapper,
                                   IotDeviceMessageService messageService,
                                   IotMessageBus messageBus,
                                   DeviceServerIdService deviceServerIdService,
                                   String serverId) {
        super(PROTOCOL_TYPE, serverId, properties, deviceMapper, messageService, messageBus, deviceServerIdService);
    }

    @Override
    protected Map<String, Object> poll(DeviceDO device, IndustrialDeviceConfig config) throws Exception {
        String endpointUrl = resolveEndpointUrl(device, config);
        String key = clientKey(endpointUrl, config);
        Object lock = clientLocks.computeIfAbsent(key, ignored -> new Object());
        synchronized (lock) {
            OpcUaClient client = acquireClientLocked(endpointUrl, config, key);
            List<IndustrialDeviceConfig.Point> configuredPoints = config.getPoints().stream()
                    .filter(point -> point != null && point.hasResolvedPropertyCode()
                            && StrUtil.isNotBlank(point.getNodeId()))
                    .toList();
            List<NodeId> nodeIds = configuredPoints.stream().map(point -> NodeId.parse(point.getNodeId())).toList();
            List<DataValue> dataValues = client.readValuesAsync(0, TimestampsToReturn.Both, nodeIds)
                    .get(requestTimeoutMs(), TimeUnit.MILLISECONDS);

            Map<String, Object> values = new LinkedHashMap<>();
            for (int index = 0; index < configuredPoints.size(); index++) {
                DataValue dataValue = dataValues.get(index);
                if (dataValue.getStatusCode() != null && dataValue.getStatusCode().isBad()) {
                    throw new IllegalStateException("OPC UA read failed for "
                            + configuredPoints.get(index).getNodeId() + ": " + dataValue.getStatusCode());
                }
                Object value = dataValue.getValue() == null ? null : dataValue.getValue().getValue();
                values.put(configuredPoints.get(index).resolvedPropertyCode(), toJsonValue(value));
            }
            return values;
        }
    }

    @Override
    protected void write(DeviceDO device, IndustrialDeviceConfig config, IotDeviceMessage message) throws Exception {
        String endpointUrl = resolveEndpointUrl(device, config);
        String key = clientKey(endpointUrl, config);
        Object lock = clientLocks.computeIfAbsent(key, ignored -> new Object());
        synchronized (lock) {
            OpcUaClient client = acquireClientLocked(endpointUrl, config, key);
            for (IndustrialDeviceConfig.Point point : config.getPoints()) {
                if (point == null || !Boolean.TRUE.equals(point.getWritable()) || StrUtil.isBlank(point.getNodeId())
                        || !point.hasResolvedPropertyCode()) {
                    continue;
                }
                Object value = IotDeviceMessageUtils.extractPropertyValue(message, point.resolvedPropertyCode());
                if (value == null) {
                    continue;
                }
                NodeId nodeId = NodeId.parse(point.getNodeId());
                DataValue dataValue = DataValue.valueOnly(new Variant(toOpcUaValue(value, point.getDataType())));
                List<StatusCode> statusCodes = client.writeValuesAsync(List.of(nodeId), List.of(dataValue))
                        .get(requestTimeoutMs(), TimeUnit.MILLISECONDS);
                StatusCode statusCode = statusCodes.get(0);
                if (statusCode.isBad()) {
                    throw new IllegalStateException("OPC UA write failed for " + point.getNodeId() + ": " + statusCode);
                }
            }
        }
    }

    private OpcUaClient acquireClientLocked(String endpointUrl, IndustrialDeviceConfig config, String key)
            throws Exception {
        OpcUaClient existing = clients.get(key);
        if (existing != null) {
            try {
                existing.connectAsync().get(requestTimeoutMs(), TimeUnit.MILLISECONDS);
                return existing;
            } catch (Exception e) {
                disconnectQuietly(existing);
                clients.remove(key, existing);
            }
        }
        OpcUaClient client = createClient(endpointUrl, config);
        client.connectAsync().get(requestTimeoutMs(), TimeUnit.MILLISECONDS);
        clients.put(key, client);
        return client;
    }

    private OpcUaClient createClient(String endpointUrl, IndustrialDeviceConfig config) throws Exception {
        boolean hasCredentials = StrUtil.isNotBlank(config.getUsername());
        return OpcUaClient.create(
                endpointUrl,
                endpoints -> endpoints.stream()
                        .filter(endpoint -> SecurityPolicy.None.getUri().equals(endpoint.getSecurityPolicyUri()))
                        .findFirst(),
                transportConfig -> {
                },
                clientConfig -> clientConfig.setIdentityProvider(hasCredentials
                        ? new UsernameProvider(config.getUsername(), StrUtil.nullToEmpty(config.getPassword()))
                        : new AnonymousProvider()));
    }

    @Override
    protected void invalidateConnection(DeviceDO device, IndustrialDeviceConfig config) {
        String endpointUrl;
        try {
            endpointUrl = resolveEndpointUrl(device, config);
        } catch (Exception e) {
            return;
        }
        String key = clientKey(endpointUrl, config);
        Object lock = clientLocks.computeIfAbsent(key, ignored -> new Object());
        synchronized (lock) {
            OpcUaClient client = clients.remove(key);
            disconnectQuietly(client);
        }
    }

    @Override
    protected void closeConnections() {
        for (OpcUaClient client : clients.values()) {
            disconnectQuietly(client);
        }
        clients.clear();
    }

    private void disconnectQuietly(OpcUaClient client) {
        if (client == null) {
            return;
        }
        try {
            client.disconnectAsync().get(Math.min(requestTimeoutMs(), 3000L), TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            log.debug("[disconnectQuietly][opcua disconnect failed]", e);
        }
    }

    private static String clientKey(String endpointUrl, IndustrialDeviceConfig config) {
        return endpointUrl + "|" + StrUtil.nullToEmpty(config.getUsername());
    }

    private Object toOpcUaValue(Object value, String dataType) {
        String type = StrUtil.blankToDefault(dataType, "AUTO").toUpperCase();
        return switch (type) {
            case "BOOLEAN" -> value instanceof Boolean bool ? bool : Boolean.parseBoolean(String.valueOf(value));
            case "INT32" -> value instanceof Number number ? number.intValue() : Integer.parseInt(String.valueOf(value));
            case "INT64" -> value instanceof Number number ? number.longValue() : Long.parseLong(String.valueOf(value));
            case "FLOAT" -> value instanceof Number number ? number.floatValue() : Float.parseFloat(String.valueOf(value));
            case "DOUBLE" -> value instanceof Number number ? number.doubleValue() : Double.parseDouble(String.valueOf(value));
            case "STRING" -> String.valueOf(value);
            default -> value;
        };
    }

    private String resolveEndpointUrl(DeviceDO device, IndustrialDeviceConfig config) {
        if (StrUtil.isNotBlank(config.getEndpointUrl())) {
            return config.getEndpointUrl();
        }
        String host = StrUtil.blankToDefault(config.getHost(), device.getIpAddress());
        if (StrUtil.isBlank(host)) {
            throw new IllegalArgumentException("OPC UA endpoint URL is missing");
        }
        return "opc.tcp://" + host + ":" + (config.getPort() == null ? 4840 : config.getPort());
    }

    private Object toJsonValue(Object value) {
        if (value == null || value instanceof Number || value instanceof Boolean || value instanceof String) {
            return value;
        }
        if (value instanceof ByteString byteString) {
            byte[] bytes = byteString.bytes();
            return bytes == null ? null : Base64.getEncoder().encodeToString(bytes);
        }
        if (value.getClass().isArray()) {
            int length = Array.getLength(value);
            List<Object> values = new ArrayList<>(length);
            for (int index = 0; index < length; index++) {
                values.add(toJsonValue(Array.get(value, index)));
            }
            return values;
        }
        return String.valueOf(value);
    }

    @Override
    protected String connectionAddress(DeviceDO device, IndustrialDeviceConfig config) {
        return StrUtil.blankToDefault(config.getEndpointUrl(),
                "opc.tcp://" + StrUtil.blankToDefault(config.getHost(), device.getIpAddress()) + ":"
                        + (config.getPort() == null ? 4840 : config.getPort()));
    }
}
