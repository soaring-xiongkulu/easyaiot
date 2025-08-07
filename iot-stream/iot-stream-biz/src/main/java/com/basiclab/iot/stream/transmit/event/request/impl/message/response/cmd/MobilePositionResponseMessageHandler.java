package com.basiclab.iot.stream.transmit.event.request.impl.message.response.cmd;

import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.DeviceChannel;
import com.basiclab.iot.stream.bean.MobilePosition;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.service.IDeviceChannelService;
import com.basiclab.iot.stream.transmit.callback.DeferredResultHolder;
import com.basiclab.iot.stream.transmit.callback.RequestMessage;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.transmit.event.request.impl.message.IMessageHandler;
import com.basiclab.iot.stream.transmit.event.request.impl.message.response.ResponseMessageHandler;
import com.basiclab.iot.stream.utils.NumericUtil;
import com.basiclab.iot.stream.utils.SipUtils;
import com.basiclab.iot.stream.utils.DateUtil;
import gov.nist.javax.sip.message.SIPRequest;
import lombok.extern.slf4j.Slf4j;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.util.ObjectUtils;

import javax.sip.InvalidArgumentException;
import javax.sip.RequestEvent;
import javax.sip.SipException;
import javax.sip.message.Response;
import java.text.ParseException;

import static com.basiclab.iot.stream.utils.XmlUtil.getText;

/**
 * 移动设备位置数据查询回复
 * @author lin
 */
@Slf4j
@Component
public class MobilePositionResponseMessageHandler extends SIPRequestProcessorParent implements InitializingBean, IMessageHandler {

    private final String cmdType = "MobilePosition";

    @Autowired
    private ResponseMessageHandler responseMessageHandler;

    @Autowired
    private IDeviceChannelService deviceChannelService;

    @Autowired
    private DeferredResultHolder resultHolder;

    @Override
    public void afterPropertiesSet() throws Exception {
        responseMessageHandler.addHandler(cmdType, this);
    }

    @Override
    public void handForDevice(RequestEvent evt, Device device, Element rootElement) {
        SIPRequest request = (SIPRequest) evt.getRequest();

        try {
            rootElement = getRootElement(evt, device.getCharset());
            if (rootElement == null) {
                log.warn("[ 移动设备位置数据查询回复 ] content cannot be null, {}", evt.getRequest());
                try {
                    responseAck(request, Response.BAD_REQUEST);
                } catch (SipException | InvalidArgumentException | ParseException e) {
                    log.error("[命令发送失败] 移动设备位置数据查询 BAD_REQUEST: {}", e.getMessage());
                }
                return;
            }
            String channelId = getText(rootElement, "DeviceID");
            DeviceChannel deviceChannel = deviceChannelService.getOne(device.getDeviceId(), channelId);
            if (deviceChannel == null) {
                log.warn("[解析报警消息] 未找到通道：{}/{}", device.getDeviceId(), channelId);
            }else {
                MobilePosition mobilePosition = new MobilePosition();
                mobilePosition.setCreateTime(DateUtil.getNow());
                if (!ObjectUtils.isEmpty(device.getName())) {
                    mobilePosition.setDeviceName(device.getName());
                }
                mobilePosition.setDeviceId(device.getDeviceId());
                mobilePosition.setChannelId(deviceChannel.getId());
                //兼容ISO 8601格式时间
                String time = getText(rootElement, "Time");
                if (ObjectUtils.isEmpty(time)){
                    mobilePosition.setTime(DateUtil.getNow());
                }else {
                    mobilePosition.setTime(SipUtils.parseTime(time));
                }
                mobilePosition.setLongitude(Double.parseDouble(getText(rootElement, "Longitude")));
                mobilePosition.setLatitude(Double.parseDouble(getText(rootElement, "Latitude")));
                if (NumericUtil.isDouble(getText(rootElement, "Speed"))) {
                    mobilePosition.setSpeed(Double.parseDouble(getText(rootElement, "Speed")));
                } else {
                    mobilePosition.setSpeed(0.0);
                }
                if (NumericUtil.isDouble(getText(rootElement, "Direction"))) {
                    mobilePosition.setDirection(Double.parseDouble(getText(rootElement, "Direction")));
                } else {
                    mobilePosition.setDirection(0.0);
                }
                if (NumericUtil.isDouble(getText(rootElement, "Altitude"))) {
                    mobilePosition.setAltitude(Double.parseDouble(getText(rootElement, "Altitude")));
                } else {
                    mobilePosition.setAltitude(0.0);
                }
                mobilePosition.setReportSource("Mobile Position");

                // 更新device channel 的经纬度
                deviceChannel.setLongitude(mobilePosition.getLongitude());
                deviceChannel.setLatitude(mobilePosition.getLatitude());
                deviceChannel.setGpsTime(mobilePosition.getTime());

                deviceChannelService.updateChannelGPS(device, deviceChannel, mobilePosition);

                String key = DeferredResultHolder.CALLBACK_CMD_MOBILE_POSITION + device.getDeviceId();
                RequestMessage msg = new RequestMessage();
                msg.setKey(key);
                msg.setData(mobilePosition);
                resultHolder.invokeAllResult(msg);
            }

            //回复 200 OK
            try {
                responseAck(request, Response.OK);
            } catch (SipException | InvalidArgumentException | ParseException e) {
                log.error("[命令发送失败] 移动设备位置数据查询 200: {}", e.getMessage());
            }

        } catch (DocumentException e) {
            log.error("未处理的异常 ", e);
        }
    }

    @Override
    public void handForPlatform(RequestEvent evt, Platform parentPlatform, Element element) {

    }
}
