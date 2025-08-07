package com.basiclab.iot.stream.transmit.event.request.impl.message.response.cmd;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.service.IDeviceService;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.transmit.event.request.impl.message.IMessageHandler;
import com.basiclab.iot.stream.transmit.event.request.impl.message.response.ResponseMessageHandler;
import com.basiclab.iot.stream.utils.XmlUtil;
import gov.nist.javax.sip.message.SIPRequest;
import lombok.extern.slf4j.Slf4j;
import org.dom4j.Element;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.sip.InvalidArgumentException;
import javax.sip.RequestEvent;
import javax.sip.SipException;
import javax.sip.message.Response;
import java.text.ParseException;

@Slf4j
@Component
public class DeviceStatusResponseMessageHandler extends SIPRequestProcessorParent implements InitializingBean, IMessageHandler {

    private final String cmdType = "DeviceStatus";

    @Autowired
    private ResponseMessageHandler responseMessageHandler;

    @Autowired
    private IDeviceService deviceService;

    @Override
    public void afterPropertiesSet() throws Exception {
        responseMessageHandler.addHandler(cmdType, this);
    }

    @Override
    public void handForDevice(RequestEvent evt, Device device, Element element) {
        log.info("接收到DeviceStatus应答消息");
        // 检查设备是否存在， 不存在则不回复
        if (device == null) {
            return;
        }
        // 回复200 OK
        try {
             responseAck((SIPRequest) evt.getRequest(), Response.OK);
        } catch (SipException | InvalidArgumentException | ParseException e) {
            log.error("[命令发送失败] 国标级联 设备状态应答回复200OK: {}", e.getMessage());
        }
        Element onlineElement = element.element("Online");
        JSONObject json = new JSONObject();
        XmlUtil.node2Json(element, json);
        if (log.isDebugEnabled()) {
            log.debug(json.toJSONString());
        }
        String text = onlineElement.getText();
        responseMessageHandler.handMessageEvent(element, text);

    }

    @Override
    public void handForPlatform(RequestEvent evt, Platform parentPlatform, Element rootElement) {


    }
}
