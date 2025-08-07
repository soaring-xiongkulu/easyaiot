package com.basiclab.iot.stream.transmit.event.request.impl.message;

import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.service.IPlatformService;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.transmit.event.request.impl.message.query.cmd.CatalogQueryMessageHandler;
import gov.nist.javax.sip.message.SIPRequest;
import lombok.extern.slf4j.Slf4j;
import org.dom4j.Element;
import org.springframework.beans.factory.annotation.Autowired;

import javax.sip.InvalidArgumentException;
import javax.sip.RequestEvent;
import javax.sip.SipException;
import javax.sip.message.Response;
import java.text.ParseException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static com.basiclab.iot.stream.utils.XmlUtil.getText;

@Slf4j
public abstract class MessageHandlerAbstract extends SIPRequestProcessorParent implements IMessageHandler{

    public Map<String, IMessageHandler> messageHandlerMap = new ConcurrentHashMap<>();

    @Autowired
    private IPlatformService platformService;

    public void addHandler(String cmdType, IMessageHandler messageHandler) {
        messageHandlerMap.put(cmdType, messageHandler);
    }

    @Override
    public void handForDevice(RequestEvent evt, Device device, Element element) {
        String cmd = getText(element, "CmdType");
        if (cmd == null) {
            try {
                responseAck((SIPRequest) evt.getRequest(), Response.OK);
            } catch (SipException | InvalidArgumentException | ParseException e) {
                log.error("[命令发送失败] 回复200 OK: {}", e.getMessage());
            }
            return;
        }
        IMessageHandler messageHandler = messageHandlerMap.get(cmd);

        if (messageHandler != null) {
            //两个国标平台互相级联时由于上一步判断导致本该在平台处理的消息 放到了设备的处理逻辑
            //所以对目录查询单独做了校验
            if(messageHandler instanceof CatalogQueryMessageHandler){
                Platform parentPlatform = platformService.queryPlatformByServerGBId(device.getDeviceId());
                messageHandler.handForPlatform(evt, parentPlatform, element);
                return;
            }
            messageHandler.handForDevice(evt, device, element);
        }
    }

    @Override
    public void handForPlatform(RequestEvent evt, Platform parentPlatform, Element element) {
        String cmd = getText(element, "CmdType");
        IMessageHandler messageHandler = messageHandlerMap.get(cmd);
        if (messageHandler != null) {
            messageHandler.handForPlatform(evt, parentPlatform, element);
        }
    }
}
