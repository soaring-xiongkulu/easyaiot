package com.basiclab.iot.stream.transmit.event.request.impl.message.query.cmd;

import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.service.IGbChannelService;
import com.basiclab.iot.stream.service.IPlatformChannelService;
import com.basiclab.iot.stream.transmit.cmd.impl.SIPCommanderForPlatform;
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
import javax.sip.header.FromHeader;
import javax.sip.message.Response;
import java.text.ParseException;
import java.util.List;

@Slf4j
@Component
public class CatalogQueryMessageHandler extends SIPRequestProcessorParent implements InitializingBean, IMessageHandler {

    private final String cmdType = "Catalog";

    @Autowired
    private QueryMessageHandler queryMessageHandler;

    @Autowired
    private IGbChannelService channelService;

    @Autowired
    private IPlatformChannelService platformChannelService;

    @Autowired
    private SIPCommanderForPlatform cmderFroPlatform;


    @Override
    public void afterPropertiesSet() throws Exception {
        queryMessageHandler.addHandler(cmdType, this);
    }

    @Override
    public void handForDevice(RequestEvent evt, Device device, Element element) {
        try {
            // 回复200 OK
            responseAck((SIPRequest) evt.getRequest(), Response.FORBIDDEN);
        } catch (SipException | InvalidArgumentException | ParseException ignored) {}
    }

    @Override
    public void handForPlatform(RequestEvent evt, Platform platform, Element rootElement) {

        FromHeader fromHeader = (FromHeader) evt.getRequest().getHeader(FromHeader.NAME);
        try {
            // 回复200 OK
             responseAck((SIPRequest) evt.getRequest(), Response.OK);
        } catch (SipException | InvalidArgumentException | ParseException e) {
            log.error("[命令发送失败] 国标级联 目录查询回复200OK: {}", e.getMessage());
        }
        Element snElement = rootElement.element("SN");
        String sn = snElement.getText();
        List<CommonGBChannel> channelList = platformChannelService.queryByPlatform(platform);

        try {
            if (!channelList.isEmpty()) {
                cmderFroPlatform.catalogQuery(channelList, platform, sn, fromHeader.getTag());
            }else {
                // 回复无通道
                cmderFroPlatform.catalogQuery(null, platform, sn, fromHeader.getTag(), 0);
            }
        } catch (SipException | InvalidArgumentException | ParseException e) {
            log.error("[命令发送失败] 国标级联 目录查询回复: {}", e.getMessage());
        }
    }
}
