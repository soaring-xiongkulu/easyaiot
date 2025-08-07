package com.basiclab.iot.stream.transmit.event.request.impl;

import com.basiclab.iot.stream.config.SipConfig;
import com.basiclab.iot.stream.bean.*;
import com.basiclab.iot.stream.event.EventPublisher;
import com.basiclab.iot.stream.service.IDeviceChannelService;
import com.basiclab.iot.stream.transmit.ISIPProcessorObserver;
import com.basiclab.iot.stream.transmit.SIPProcessorObserver;
import com.basiclab.iot.stream.transmit.event.request.ISIPRequestProcessor;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.utils.NumericUtil;
import com.basiclab.iot.stream.utils.SipUtils;
import com.basiclab.iot.stream.utils.XmlUtil;
import com.basiclab.iot.stream.storager.IRedisCatchStorage;
import com.basiclab.iot.stream.utils.DateUtil;
import gov.nist.javax.sip.message.SIPRequest;
import lombok.extern.slf4j.Slf4j;
import org.dom4j.DocumentException;
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

/**
 * SIP命令类型： NOTIFY请求,这是作为上级发送订阅请求后，设备才会响应的
 */
@Slf4j
@Component
public class NotifyRequestProcessor extends SIPRequestProcessorParent implements InitializingBean, ISIPRequestProcessor {

	@Autowired
	private SipConfig sipConfig;

	@Autowired
	private IRedisCatchStorage redisCatchStorage;

	@Autowired
	private EventPublisher publisher;

	private final String method = "NOTIFY";

	@Autowired
	private ISIPProcessorObserver sipProcessorObserver;

	@Autowired
	private IDeviceChannelService deviceChannelService;

	@Autowired
	private NotifyRequestForCatalogProcessor notifyRequestForCatalogProcessor;

	@Autowired
	private NotifyRequestForMobilePositionProcessor notifyRequestForMobilePositionProcessor;

	@Override
	public void afterPropertiesSet() throws Exception {
		// 添加消息处理的订阅
		sipProcessorObserver.addRequestProcessor(method, this);
	}

	@Override
	public void process(RequestEvent evt) {
		try {
			responseAck((SIPRequest) evt.getRequest(), Response.OK, null, null);
			Element rootElement = getRootElement(evt);
			if (rootElement == null) {
				log.error("处理NOTIFY消息时未获取到消息体,{}", evt.getRequest());
				responseAck((SIPRequest) evt.getRequest(), Response.OK, null, null);
				return;
			}
			String cmd = XmlUtil.getText(rootElement, "CmdType");

			if (CmdType.CATALOG.equals(cmd)) {
				notifyRequestForCatalogProcessor.process(evt);
			} else if (CmdType.ALARM.equals(cmd)) {
				processNotifyAlarm(evt);
			} else if (CmdType.MOBILE_POSITION.equals(cmd)) {
				notifyRequestForMobilePositionProcessor.process(evt);
			} else {
				log.info("接收到消息：" + cmd);
			}
		} catch (SipException | InvalidArgumentException | ParseException e) {
			log.error("未处理的异常 ", e);
		} catch (DocumentException e) {
			throw new RuntimeException(e);
		}

	}
	/***
	 * 处理alarm设备报警Notify
	 */
	private void processNotifyAlarm(RequestEvent evt) {
		if (!sipConfig.isAlarm()) {
			return;
		}
		try {
			FromHeader fromHeader = (FromHeader) evt.getRequest().getHeader(FromHeader.NAME);
			String deviceId = SipUtils.getUserIdFromFromHeader(fromHeader);

			Element rootElement = getRootElement(evt);
			if (rootElement == null) {
				log.error("处理alarm设备报警Notify时未获取到消息体{}", evt.getRequest());
				return;
			}
			Element deviceIdElement = rootElement.element("DeviceID");
			String channelId = deviceIdElement.getText().toString();

			Device device = redisCatchStorage.getDevice(deviceId);
			if (device == null) {
				log.warn("[ NotifyAlarm ] 未找到设备：{}", deviceId);
				return;
			}
			rootElement = getRootElement(evt, device.getCharset());
			if (rootElement == null) {
				log.warn("[ NotifyAlarm ] content cannot be null, {}", evt.getRequest());
				return;
			}
			DeviceAlarm deviceAlarm = new DeviceAlarm();
			deviceAlarm.setDeviceId(deviceId);
			deviceAlarm.setDeviceName(device.getName());
			deviceAlarm.setAlarmPriority(XmlUtil.getText(rootElement, "AlarmPriority"));
			deviceAlarm.setAlarmMethod(XmlUtil.getText(rootElement, "AlarmMethod"));
			String alarmTime = XmlUtil.getText(rootElement, "AlarmTime");
			if (alarmTime == null) {
				log.warn("[ NotifyAlarm ] AlarmTime cannot be null");
				return;
			}
			deviceAlarm.setAlarmTime(DateUtil.ISO8601Toyyyy_MM_dd_HH_mm_ss(alarmTime));
			if (XmlUtil.getText(rootElement, "AlarmDescription") == null) {
				deviceAlarm.setAlarmDescription("");
			} else {
				deviceAlarm.setAlarmDescription(XmlUtil.getText(rootElement, "AlarmDescription"));
			}
			if (NumericUtil.isDouble(XmlUtil.getText(rootElement, "Longitude"))) {
				deviceAlarm.setLongitude(Double.parseDouble(XmlUtil.getText(rootElement, "Longitude")));
			} else {
				deviceAlarm.setLongitude(0.00);
			}
			if (NumericUtil.isDouble(XmlUtil.getText(rootElement, "Latitude"))) {
				deviceAlarm.setLatitude(Double.parseDouble(XmlUtil.getText(rootElement, "Latitude")));
			} else {
				deviceAlarm.setLatitude(0.00);
			}
			log.info("[收到Notify-Alarm]：{}/{}", device.getDeviceId(), deviceAlarm.getChannelId());
			if ("4".equals(deviceAlarm.getAlarmMethod())) {
				DeviceChannel deviceChannel = deviceChannelService.getOne(device.getDeviceId(), channelId);
				if (deviceChannel == null) {
					log.warn("[解析报警通知] 未找到通道：{}/{}", device.getDeviceId(), channelId);
				}else {
					MobilePosition mobilePosition = new MobilePosition();
					mobilePosition.setChannelId(deviceChannel.getId());
					mobilePosition.setCreateTime(DateUtil.getNow());
					mobilePosition.setDeviceId(deviceAlarm.getDeviceId());
					mobilePosition.setTime(deviceAlarm.getAlarmTime());
					mobilePosition.setLongitude(deviceAlarm.getLongitude());
					mobilePosition.setLatitude(deviceAlarm.getLatitude());
					mobilePosition.setReportSource("GPS Alarm");

					// 更新device channel 的经纬度
					deviceChannel.setLongitude(mobilePosition.getLongitude());
					deviceChannel.setLatitude(mobilePosition.getLatitude());
					deviceChannel.setGpsTime(mobilePosition.getTime());

					deviceChannelService.updateChannelGPS(device, deviceChannel, mobilePosition);
				}
			}

			// 回复200 OK
			if (redisCatchStorage.deviceIsOnline(deviceId)) {
				publisher.deviceAlarmEventPublish(deviceAlarm);
			}
		} catch (DocumentException e) {
			log.error("未处理的异常 ", e);
		}
	}


}
