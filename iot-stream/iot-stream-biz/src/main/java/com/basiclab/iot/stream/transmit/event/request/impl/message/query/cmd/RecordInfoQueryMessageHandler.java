package com.basiclab.iot.stream.transmit.event.request.impl.message.query.cmd;

import com.basiclab.iot.stream.common.enums.ChannelDataType;
import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.DeviceChannel;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.event.record.RecordInfoEventListener;
import com.basiclab.iot.stream.service.IDeviceChannelService;
import com.basiclab.iot.stream.service.IDeviceService;
import com.basiclab.iot.stream.service.IGbChannelService;
import com.basiclab.iot.stream.transmit.cmd.impl.SIPCommander;
import com.basiclab.iot.stream.transmit.cmd.impl.SIPCommanderForPlatform;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.transmit.event.request.impl.message.IMessageHandler;
import com.basiclab.iot.stream.transmit.event.request.impl.message.query.QueryMessageHandler;
import com.basiclab.iot.stream.utils.DateUtil;
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
public class RecordInfoQueryMessageHandler extends SIPRequestProcessorParent implements InitializingBean, IMessageHandler {

    private final String cmdType = "RecordInfo";

    @Autowired
    private QueryMessageHandler queryMessageHandler;

    @Autowired
    private IGbChannelService channelService;

    @Autowired
    private IDeviceService deviceService;

    @Autowired
    private IDeviceChannelService deviceChannelService;

    @Autowired
    private SIPCommanderForPlatform cmderFroPlatform;

    @Autowired
    private SIPCommander commander;

    @Autowired
    private RecordInfoEventListener recordInfoEventListener;

    @Override
    public void afterPropertiesSet() throws Exception {
        queryMessageHandler.addHandler(cmdType, this);
    }

    @Override
    public void handForDevice(RequestEvent evt, Device device, Element element) {

    }

    @Override
    public void handForPlatform(RequestEvent evt, Platform platform, Element rootElement) {

        SIPRequest request = (SIPRequest) evt.getRequest();
        Element snElement = rootElement.element("SN");
        int sn = Integer.parseInt(snElement.getText());
        Element deviceIDElement = rootElement.element("DeviceID");
        String channelId = deviceIDElement.getText();
        Element startTimeElement = rootElement.element("StartTime");
        String startTime = null;
        if (startTimeElement != null) {
            startTime = startTimeElement.getText();
        }
        Element endTimeElement = rootElement.element("EndTime");
        String endTime = null;
        if (endTimeElement != null) {
            endTime = endTimeElement.getText();
        }
        Element secrecyElement = rootElement.element("Secrecy");
        int secrecy = 0;
        if (secrecyElement != null) {
            secrecy = Integer.parseInt(secrecyElement.getText().trim());
        }
        String type = "all";
        Element typeElement = rootElement.element("Type");
        if (typeElement != null) {
            type =  typeElement.getText();
        }

        // 向国标设备请求录像数据
        CommonGBChannel channel = channelService.queryOneWithPlatform(platform.getId(), channelId);
        if (channel == null) {
            log.info("[平台查询录像记录] 未找到通道 {}/{}", platform.getName(), channelId );
            try {
                responseAck(request, Response.BAD_REQUEST);
            } catch (SipException | InvalidArgumentException | ParseException e) {
                log.error("[命令发送失败] [平台查询录像记录] 未找到通道: {}", e.getMessage());
            }
            return;
        }
        if (channel.getDataType() != ChannelDataType.GB28181.value) {
            log.info("[平台查询录像记录] 只支持查询国标28181的录像数据 {}/{}", platform.getName(), channelId );
            try {
                responseAck(request, Response.NOT_IMPLEMENTED); // 回复未实现
            } catch (SipException | InvalidArgumentException | ParseException e) {
                log.error("[命令发送失败] 平台查询录像记录: {}", e.getMessage());
            }
            return;
        }
        Device device = deviceService.getDevice(channel.getDataDeviceId());
        if (device == null) {
            log.warn("[平台查询录像记录] 未找到通道对应的设备 {}/{}", platform.getName(), channelId );
            try {
                responseAck(request, Response.BAD_REQUEST);
            } catch (SipException | InvalidArgumentException | ParseException e) {
                log.error("[命令发送失败] [平台查询录像记录] 未找到通道对应的设备: {}", e.getMessage());
            }
            return;
        }
        // 获取通道的原始信息
        DeviceChannel deviceChannel = deviceChannelService.getOneForSourceById(channel.getGbId());
        // 接收录像数据
        recordInfoEventListener.addEndEventHandler(device.getDeviceId(), deviceChannel.getDeviceId(), (recordInfo)->{
            try {
                log.info("[国标级联] 录像查询收到数据， 通道： {}，准备转发===", channelId);
                cmderFroPlatform.recordInfo(channel, platform, request.getFromTag(), recordInfo);
            } catch (SipException | InvalidArgumentException | ParseException e) {
                log.error("[命令发送失败] 国标级联 回复录像数据: {}", e.getMessage());
            }
        });
        try {
            commander.recordInfoQuery(device, deviceChannel.getDeviceId(), DateUtil.ISO8601Toyyyy_MM_dd_HH_mm_ss(startTime),
                    DateUtil.ISO8601Toyyyy_MM_dd_HH_mm_ss(endTime), sn, secrecy, type, (eventResult -> {
                        // 回复200 OK
                        try {
                            responseAck(request, Response.OK);
                        } catch (SipException | InvalidArgumentException | ParseException e) {
                            log.error("[命令发送失败] 录像查询回复: {}", e.getMessage());
                        }
                    }),(eventResult -> {
                        // 查询失败
                        try {
                            responseAck(request, eventResult.statusCode, eventResult.msg);
                        } catch (SipException | InvalidArgumentException | ParseException e) {
                            log.error("[命令发送失败] 录像查询回复: {}", e.getMessage());
                        }
                    }));
        } catch (InvalidArgumentException | ParseException | SipException e) {
            log.error("[命令发送失败] 录像查询: {}", e.getMessage());
        }
    }
}
