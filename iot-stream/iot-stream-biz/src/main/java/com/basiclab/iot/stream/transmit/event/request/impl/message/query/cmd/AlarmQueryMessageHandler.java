package com.basiclab.iot.stream.transmit.event.request.impl.message.query.cmd;

import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.transmit.event.request.impl.message.IMessageHandler;
import com.basiclab.iot.stream.transmit.event.request.impl.message.query.QueryMessageHandler;
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
public class AlarmQueryMessageHandler extends SIPRequestProcessorParent implements InitializingBean, IMessageHandler {

    private final String cmdType = "Alarm";

    @Autowired
    private QueryMessageHandler queryMessageHandler;

    @Override
    public void afterPropertiesSet() throws Exception {
        queryMessageHandler.addHandler(cmdType, this);
    }

    @Override
    public void handForDevice(RequestEvent evt, Device device, Element element) {

    }

    @Override
    public void handForPlatform(RequestEvent evt, Platform parentPlatform, Element rootElement) {

        log.info("不支持alarm查询");
        try {
             responseAck((SIPRequest) evt.getRequest(), Response.NOT_FOUND, "not support alarm query");
        } catch (SipException | InvalidArgumentException | ParseException e) {
            log.error("[命令发送失败] 国标级联 alarm查询回复200OK: {}", e.getMessage());
        }

    }
}
