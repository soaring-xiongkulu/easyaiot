package com.basiclab.iot.sink.protocol.tcp.router;

import cn.hutool.core.map.MapUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.auth.service.DeviceAuthService;
import com.basiclab.iot.sink.biz.dto.IotDeviceAuthReqDTO;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceAuthUtils;
import com.basiclab.iot.sink.codec.tcp.IotTcpBinaryDeviceMessageCodec;
import com.basiclab.iot.sink.codec.tcp.IotTcpJsonDeviceMessageCodec;
import com.basiclab.iot.sink.protocol.tcp.IotTcpUpstreamProtocol;
import com.basiclab.iot.sink.protocol.tcp.manager.IotTcpConnectionManager;
import com.basiclab.iot.sink.messagebus.publisher.IotDeviceService;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import io.vertx.core.Handler;
import io.vertx.core.buffer.Buffer;
import io.vertx.core.net.NetSocket;
import lombok.extern.slf4j.Slf4j;

/**
 * IotTcpUpstreamHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
public class IotTcpUpstreamHandler implements Handler<NetSocket> {

    private static final String CODEC_TYPE_JSON = IotTcpJsonDeviceMessageCodec.TYPE;
    private static final String CODEC_TYPE_BINARY = IotTcpBinaryDeviceMessageCodec.TYPE;

    private static final String AUTH_METHOD = "auth";

    private final IotDeviceMessageService deviceMessageService;

    private final IotDeviceService deviceService;

    private final IotTcpConnectionManager connectionManager;

    private final DeviceAuthService deviceAuthService;

    private final String serverId;

    public IotTcpUpstreamHandler(IotTcpUpstreamProtocol protocol,
                                 IotDeviceMessageService deviceMessageService,
                                 IotDeviceService deviceService,
                                 IotTcpConnectionManager connectionManager) {
        this.deviceMessageService = deviceMessageService;
        this.deviceService = deviceService;
        this.connectionManager = connectionManager;
        this.deviceAuthService = SpringUtil.getBean(DeviceAuthService.class);
        this.serverId = protocol.getServerId();
    }

    @Override
    public void handle(NetSocket socket) {
        String clientId = IdUtil.simpleUUID();
        log.debug("[handle][设备连接，客户端 ID: {}，地址: {}]", clientId, socket.remoteAddress());

        // 设置异常和关闭处理器
        socket.exceptionHandler(ex -> {
            log.warn("[handle][连接异常，客户端 ID: {}，地址: {}]", clientId, socket.remoteAddress());
            cleanupConnection(socket);
        });
        socket.closeHandler(v -> {
            log.debug("[handle][连接关闭，客户端 ID: {}，地址: {}]", clientId, socket.remoteAddress());
            cleanupConnection(socket);
        });

        // 设置消息处理器
        socket.handler(buffer -> {
            try {
                processMessage(clientId, buffer, socket);
            } catch (Exception e) {
                log.error("[handle][消息解码失败，断开连接，客户端 ID: {}，地址: {}，错误: {}]",
                        clientId, socket.remoteAddress(), e.getMessage());
                cleanupConnection(socket);
                socket.close();
            }
        });
    }

    /**
     * 处理消息
     *
     * @param clientId 客户端 ID
     * @param buffer   消息
     * @param socket   网络连接
     * @throws Exception 消息解码失败时抛出异常
     */
    private void processMessage(String clientId, Buffer buffer, NetSocket socket) throws Exception {
        // 1. 基础检查
        if (buffer == null || buffer.length() == 0) {
            return;
        }

        // 2. 获取连接信息（用于构建 topic）
        IotTcpConnectionManager.ConnectionInfo connectionInfo = connectionManager.getConnectionInfo(socket);
        String productIdentification = null;
        String deviceIdentification = null;
        if (connectionInfo != null && connectionInfo.isAuthenticated()) {
            productIdentification = connectionInfo.getProductIdentification();
            deviceIdentification = connectionInfo.getDeviceIdentification();
        }

        // 3. 解码消息
        IotDeviceMessage message;
        try {
            byte[] bytes = buffer.getBytes();
            // 如果已认证，使用 topic 方式解码；否则使用默认方式
            if (productIdentification != null && deviceIdentification != null) {
                // 构建 topic（TCP 协议使用 /tcp/{productIdentification}/{deviceIdentification}/... 格式）
                // 先使用 unknown 作为 method，解码后再更新
                String topicForDecode = "/tcp/" + productIdentification + "/" + deviceIdentification + "/unknown";
                message = deviceMessageService.decodeDeviceMessageByTopic(bytes, topicForDecode);
            } else {
                // 未认证时，使用默认方式（需要先检测消息格式）
                boolean isBinary = IotTcpBinaryDeviceMessageCodec.isBinaryFormatQuick(bytes);
                // 构建临时 topic（使用默认格式）
                String defaultTopic = "/tcp/unknown/unknown/unknown";
                message = deviceMessageService.decodeDeviceMessageByTopic(bytes, defaultTopic);
            }
            if (message == null) {
                throw new Exception("解码后消息为空");
            }
        } catch (Exception e) {
            // 消息格式错误时抛出异常，由上层处理连接断开
            throw new Exception("消息解码失败: " + e.getMessage(), e);
        }

        // 4. 根据消息类型路由处理
        try {
            if (AUTH_METHOD.equals(message.getMethod())) {
                // 认证请求
                handleAuthenticationRequest(clientId, message, socket);
            } else {
                // 业务消息
                handleBusinessRequest(clientId, message, socket);
            }
        } catch (Exception e) {
            log.error("[processMessage][处理消息失败，客户端 ID: {}，消息方法: {}]",
                    clientId, message.getMethod(), e);
            // 发送错误响应，避免客户端一直等待
            try {
                String codecType = detectCodecTypeFromMessage(message);
                sendErrorResponse(socket, message.getRequestId(), "消息处理失败", codecType);
            } catch (Exception responseEx) {
                log.error("[processMessage][发送错误响应失败，客户端 ID: {}]", clientId, responseEx);
            }
        }
    }

    /**
     * 处理认证请求
     *
     * @param clientId  客户端 ID
     * @param message   消息信息
     * @param socket    网络连接
     */
    private void handleAuthenticationRequest(String clientId, IotDeviceMessage message, NetSocket socket) {
        try {
            // 1.1 解析认证参数
            IotDeviceAuthReqDTO authParams = parseAuthParams(message.getParams());
            if (authParams == null) {
                log.warn("[handleAuthenticationRequest][认证参数解析失败，客户端 ID: {}]", clientId);
                // 检测消息格式以确定编解码器
                String codecType = detectCodecTypeFromMessage(message);
                sendErrorResponse(socket, message.getRequestId(), "认证参数不完整", codecType);
                return;
            }
            // 1.2 执行认证
            if (!validateDeviceAuth(authParams)) {
                log.warn("[handleAuthenticationRequest][认证失败，客户端 ID: {}，username: {}]",
                        clientId, authParams.getUsername());
                String codecType = detectCodecTypeFromMessage(message);
                sendErrorResponse(socket, message.getRequestId(), "认证失败", codecType);
                return;
            }

            // 2.1 解析设备信息
            IotDeviceAuthUtils.DeviceInfo deviceInfo = IotDeviceAuthUtils.parseUsername(authParams.getUsername());
            if (deviceInfo == null) {
                String codecType = detectCodecTypeFromMessage(message);
                sendErrorResponse(socket, message.getRequestId(), "解析设备信息失败", codecType);
                return;
            }
            // 2.2 获取设备信息
            IotDeviceRespDTO device = deviceService.getDeviceFromCache(deviceInfo.getProductIdentification(),
                    deviceInfo.getDeviceIdentification());
            if (device == null) {
                String codecType = detectCodecTypeFromMessage(message);
                sendErrorResponse(socket, message.getRequestId(), "设备不存在", codecType);
                return;
            }

            // 3.1 检测消息格式以确定编解码器类型（用于后续消息处理）
            String codecType = detectCodecTypeFromMessage(message);
            // 3.2 注册连接
            registerConnection(socket, device, clientId, codecType);
            // 3.3 发送上线消息
            sendOnlineMessage(device);
            // 3.4 发送成功响应
            sendSuccessResponse(socket, message.getRequestId(), "认证成功", codecType);
            log.info("[handleAuthenticationRequest][认证成功，设备 ID: {}，设备唯一标识: {}]",
                    device.getId(), device.getDeviceIdentification());
        } catch (Exception e) {
            log.error("[handleAuthenticationRequest][认证处理异常，客户端 ID: {}]", clientId, e);
            String codecType = detectCodecTypeFromMessage(message);
            sendErrorResponse(socket, message.getRequestId(), "认证处理异常", codecType);
        }
    }

    /**
     * 处理业务请求
     *
     * @param clientId  客户端 ID
     * @param message   消息信息
     * @param socket    网络连接
     */
    private void handleBusinessRequest(String clientId, IotDeviceMessage message, NetSocket socket) {
        try {
            // 1. 检查认证状态
            if (connectionManager.isNotAuthenticated(socket)) {
                log.warn("[handleBusinessRequest][设备未认证，客户端 ID: {}]", clientId);
                String codecType = detectCodecTypeFromMessage(message);
                sendErrorResponse(socket, message.getRequestId(), "请先进行认证", codecType);
                return;
            }

            // 2. 获取认证信息并处理业务消息
            IotTcpConnectionManager.ConnectionInfo connectionInfo = connectionManager.getConnectionInfo(socket);

            // 3. 发送消息到消息总线
            deviceMessageService.sendDeviceMessage(message, connectionInfo.getProductIdentification(),
                    connectionInfo.getDeviceIdentification(), serverId);
            log.info("[handleBusinessRequest][发送消息到消息总线，客户端 ID: {}，消息: {}",
                    clientId, message.toString());
        } catch (Exception e) {
            log.error("[handleBusinessRequest][业务请求处理异常，客户端 ID: {}]", clientId, e);
        }
    }

    /**
     * 从消息中检测编解码类型（用于响应消息的编码）
     *
     * @param message 消息
     * @return 消息编解码类型
     */
    private String detectCodecTypeFromMessage(IotDeviceMessage message) {
        // 根据消息的 topic 判断编解码类型
        String topic = message.getTopic();
        if (StrUtil.isNotBlank(topic) && topic.startsWith("/tcp/")) {
            // 可以根据 topic 进一步判断是二进制还是 JSON
            // 这里简化处理，默认使用 JSON（实际应该根据消息内容判断）
            return CODEC_TYPE_JSON;
        }
        // 默认使用 JSON
        return CODEC_TYPE_JSON;
    }

    /**
     * 注册连接信息
     *
     * @param socket    网络连接
     * @param device    设备
     * @param clientId  客户端 ID
     * @param codecType 消息编解码类型（用于响应消息编码）
     */
    private void registerConnection(NetSocket socket, IotDeviceRespDTO device,
                                    String clientId, String codecType) {
        IotTcpConnectionManager.ConnectionInfo connectionInfo = new IotTcpConnectionManager.ConnectionInfo()
                .setDeviceId(device.getId())
                .setProductIdentification(device.getProductIdentification())
                .setDeviceIdentification(device.getDeviceIdentification())
                .setClientId(clientId)
                .setCodecType(codecType) // 保留用于响应消息编码
                .setAuthenticated(true);
        // 注册连接
        connectionManager.registerConnection(socket, device.getId(), connectionInfo);
        
        // 存储设备与 serverId 的映射到 Redis
        DeviceServerIdService deviceServerIdService = SpringUtil.getBean(DeviceServerIdService.class);
        if (deviceServerIdService != null) {
            deviceServerIdService.saveDeviceServerId(device.getId(), serverId);
        }
    }

    /**
     * 发送设备上线消息
     *
     * @param device 设备信息
     */
    private void sendOnlineMessage(IotDeviceRespDTO device) {
        try {
            IotDeviceMessage onlineMessage = IotDeviceMessage.buildStateUpdateOnline();
            deviceMessageService.sendDeviceMessage(onlineMessage, device.getProductIdentification(),
                    device.getDeviceIdentification(), serverId);
        } catch (Exception e) {
            log.error("[sendOnlineMessage][发送上线消息失败，设备: {}]", device.getDeviceIdentification(), e);
        }
    }

    /**
     * 清理连接
     *
     * @param socket 网络连接
     */
    private void cleanupConnection(NetSocket socket) {
        try {
            // 1. 发送离线消息（如果已认证）
            IotTcpConnectionManager.ConnectionInfo connectionInfo = connectionManager.getConnectionInfo(socket);
            if (connectionInfo != null) {
                IotDeviceMessage offlineMessage = IotDeviceMessage.buildStateOffline();
                deviceMessageService.sendDeviceMessage(offlineMessage, connectionInfo.getProductIdentification(),
                        connectionInfo.getDeviceIdentification(), serverId);
                
                // 删除设备与 serverId 的映射
                DeviceServerIdService deviceServerIdService = SpringUtil.getBean(DeviceServerIdService.class);
                if (deviceServerIdService != null) {
                    deviceServerIdService.removeDeviceServerId(connectionInfo.getDeviceId());
                }
            }

            // 2. 注销连接
            connectionManager.unregisterConnection(socket);
        } catch (Exception e) {
            log.error("[cleanupConnection][清理连接失败]", e);
        }
    }

    /**
     * 发送响应消息
     *
     * @param socket    网络连接
     * @param success   是否成功
     * @param message   消息
     * @param requestId 请求 ID
     * @param codecType 消息编解码类型（用于确定编码方式）
     */
    private void sendResponse(NetSocket socket, boolean success, String message, String requestId, String codecType) {
        try {
            Object responseData = MapUtil.builder()
                    .put("success", success)
                    .put("message", message)
                    .build();

            int code = success ? 0 : 401;
            IotDeviceMessage responseMessage = IotDeviceMessage.replyOf(requestId, AUTH_METHOD, responseData,
                    code, message);

            // 获取连接信息以构建 topic
            IotTcpConnectionManager.ConnectionInfo connectionInfo = connectionManager.getConnectionInfo(socket);
            String productIdentification = connectionInfo != null ? connectionInfo.getProductIdentification() : "unknown";
            String deviceIdentification = connectionInfo != null ? connectionInfo.getDeviceIdentification() : "unknown";
            
            // 构建 topic 用于编码
            String topic = "/tcp/" + productIdentification + "/" + deviceIdentification + "/" + AUTH_METHOD;
            responseMessage.setTopic(topic);
            
            byte[] encodedData = deviceMessageService.encodeDeviceMessage(responseMessage, productIdentification, deviceIdentification);
            socket.write(Buffer.buffer(encodedData));

        } catch (Exception e) {
            log.error("[sendResponse][发送响应失败，requestId: {}]", requestId, e);
        }
    }

    /**
     * 验证设备认证信息
     *
     * @param authParams 认证参数
     * @return 是否认证成功
     */
    private boolean validateDeviceAuth(IotDeviceAuthReqDTO authParams) {
        try {
            return deviceAuthService.authDevice(new IotDeviceAuthReqDTO()
                    .setClientId(authParams.getClientId()).setUsername(authParams.getUsername())
                    .setPassword(authParams.getPassword()));
        } catch (Exception e) {
            log.error("[validateDeviceAuth][设备认证异常，username: {}]", authParams.getUsername(), e);
            return false;
        }
    }

    /**
     * 发送错误响应
     *
     * @param socket       网络连接
     * @param requestId    请求 ID
     * @param errorMessage 错误消息
     * @param codecType    消息编解码类型
     */
    private void sendErrorResponse(NetSocket socket, String requestId, String errorMessage, String codecType) {
        sendResponse(socket, false, errorMessage, requestId, codecType);
    }

    /**
     * 发送成功响应
     *
     * @param socket    网络连接
     * @param requestId 请求 ID
     * @param message   消息
     * @param codecType 消息编解码类型
     */
    @SuppressWarnings("SameParameterValue")
    private void sendSuccessResponse(NetSocket socket, String requestId, String message, String codecType) {
        sendResponse(socket, true, message, requestId, codecType);
    }

    /**
     * 解析认证参数
     *
     * @param params 参数对象（通常为 Map 类型）
     * @return 认证参数 DTO，解析失败时返回 null
     */
    @SuppressWarnings("unchecked")
    private IotDeviceAuthReqDTO parseAuthParams(Object params) {
        if (params == null) {
            return null;
        }

        try {
            // 参数默认为 Map 类型，直接转换
            if (params instanceof java.util.Map) {
                java.util.Map<String, Object> paramMap = (java.util.Map<String, Object>) params;
                return new IotDeviceAuthReqDTO()
                        .setClientId(MapUtil.getStr(paramMap, "clientId"))
                        .setUsername(MapUtil.getStr(paramMap, "username"))
                        .setPassword(MapUtil.getStr(paramMap, "password"));
            }

            // 如果已经是目标类型，直接返回
            if (params instanceof IotDeviceAuthReqDTO) {
                return (IotDeviceAuthReqDTO) params;
            }

            // 其他情况尝试 JSON 转换
            String jsonStr = JsonUtils.toJsonString(params);
            return JsonUtils.parseObject(jsonStr, IotDeviceAuthReqDTO.class);
        } catch (Exception e) {
            log.error("[parseAuthParams][解析认证参数({})失败]", params, e);
            return null;
        }
    }

}