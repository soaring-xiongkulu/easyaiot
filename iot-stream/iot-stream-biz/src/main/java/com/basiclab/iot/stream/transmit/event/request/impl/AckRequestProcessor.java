package com.basiclab.iot.stream.transmit.event.request.impl;

import com.basiclab.iot.stream.config.DynamicTask;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.exception.ControllerException;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.DeviceChannel;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.bean.SendRtpInfo;
import com.basiclab.iot.stream.service.IDeviceChannelService;
import com.basiclab.iot.stream.service.IDeviceService;
import com.basiclab.iot.stream.service.IPlatformService;
import com.basiclab.iot.stream.service.IPlayService;
import com.basiclab.iot.stream.transmit.ISIPProcessorObserver;
import com.basiclab.iot.stream.transmit.SIPProcessorObserver;
import com.basiclab.iot.stream.transmit.event.request.ISIPRequestProcessor;
import com.basiclab.iot.stream.transmit.event.request.SIPRequestProcessorParent;
import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.media.service.IMediaServerService;
import com.basiclab.iot.stream.service.ISendRtpServerService;
import com.basiclab.iot.stream.service.redisMsg.IRedisRpcService;
import com.basiclab.iot.stream.storager.IRedisCatchStorage;
import com.basiclab.iot.stream.vmanager.bean.WVPResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.sip.RequestEvent;
import javax.sip.address.SipURI;
import javax.sip.header.CallIdHeader;
import javax.sip.header.FromHeader;
import javax.sip.header.HeaderAddress;
import javax.sip.header.ToHeader;

/**
 * SIP命令类型： ACK请求
 * @author lin
 */
@Slf4j
@Component
public class AckRequestProcessor extends SIPRequestProcessorParent implements InitializingBean, ISIPRequestProcessor {

	private final String method = "ACK";

	@Autowired
	private ISIPProcessorObserver sipProcessorObserver;

	@Override
	public void afterPropertiesSet() throws Exception {
		// 添加消息处理的订阅
		sipProcessorObserver.addRequestProcessor(method, this);
	}

	@Autowired
    private IRedisCatchStorage redisCatchStorage;

	@Autowired
    private IRedisRpcService redisRpcService;

	@Autowired
    private UserSetting userSetting;

	@Autowired
	private IPlatformService platformService;

	@Autowired
	private IDeviceService deviceService;

	@Autowired
	private IDeviceChannelService deviceChannelService;

	@Autowired
	private IMediaServerService mediaServerService;

	@Autowired
	private DynamicTask dynamicTask;

	@Autowired
	private IPlayService playService;

	@Autowired
	private ISendRtpServerService sendRtpServerService;


	/**   
	 * 处理  ACK请求
	 */
	@Override
	public void process(RequestEvent evt) {
		CallIdHeader callIdHeader = (CallIdHeader)evt.getRequest().getHeader(CallIdHeader.NAME);
		dynamicTask.stop(callIdHeader.getCallId());
		String fromUserId = ((SipURI) ((HeaderAddress) evt.getRequest().getHeader(FromHeader.NAME)).getAddress().getURI()).getUser();
		String toUserId = ((SipURI) ((HeaderAddress) evt.getRequest().getHeader(ToHeader.NAME)).getAddress().getURI()).getUser();
		log.info("[收到ACK]： 来自->{}", fromUserId);
		SendRtpInfo sendRtpItem =  sendRtpServerService.queryByCallId(callIdHeader.getCallId());
		if (sendRtpItem == null) {
			log.warn("[收到ACK]：未找到来自{}，callId: {}", fromUserId, callIdHeader.getCallId());
			return;
		}
		// tcp主动时，此时是级联下级平台，在回复200ok时，本地已经请求zlm开启监听，跳过下面步骤
		if (sendRtpItem.isTcpActive()) {
			log.info("收到ACK，rtp/{} TCP主动方式等收到上级连接后开始发流", sendRtpItem.getStream());
			return;
		}
		MediaServer mediaServer = mediaServerService.getOne(sendRtpItem.getMediaServerId());
		log.info("收到ACK，rtp/{}开始向上级推流, 目标={}:{}，SSRC={}, 协议:{}",
				sendRtpItem.getStream(),
				sendRtpItem.getIp(),
				sendRtpItem.getPort(),
				sendRtpItem.getSsrc(),
				sendRtpItem.isTcp()?(sendRtpItem.isTcpActive()?"TCP主动":"TCP被动"):"UDP"
		);
		Platform parentPlatform = platformService.queryPlatformByServerGBId(fromUserId);

		if (parentPlatform != null) {
			DeviceChannel deviceChannel = deviceChannelService.getOneForSourceById(sendRtpItem.getChannelId());
			if (!userSetting.getServerId().equals(sendRtpItem.getServerId())) {
				WVPResult wvpResult = redisRpcService.startSendRtp(callIdHeader.getCallId(), sendRtpItem);
				if (wvpResult.getCode() == 0) {
					redisCatchStorage.sendPlatformStartPlayMsg(sendRtpItem, deviceChannel, parentPlatform);
				}
			} else {
				try {
					if (mediaServer != null) {
						if (sendRtpItem.isTcpActive()) {
							mediaServerService.startSendRtpPassive(mediaServer,sendRtpItem, null);
						} else {
							mediaServerService.startSendRtp(mediaServer, sendRtpItem);
						}
					}else {
						// mediaInfo 在集群的其他wvp里

					}

					redisCatchStorage.sendPlatformStartPlayMsg(sendRtpItem, deviceChannel, parentPlatform);
				}catch (ControllerException e) {
					log.error("RTP推流失败: {}", e.getMessage());
					playService.startSendRtpStreamFailHand(sendRtpItem, parentPlatform, callIdHeader);
				}
			}
		}else {
			Device device = deviceService.getDeviceByDeviceId(fromUserId);
			if (device == null) {
				log.warn("[收到ACK]：来自{}，目标为({})的推流信息为找到流体服务[{}]信息",fromUserId, toUserId, sendRtpItem.getMediaServerId());
				return;
			}
			// 设置为收到ACK后发送语音的设备已经在发送200OK开始发流了
			if (!device.isBroadcastPushAfterAck()) {
				return;
			}
			if (mediaServer == null) {
				log.warn("[收到ACK]：来自{}，目标为({})的推流信息为找到流体服务[{}]信息",fromUserId, toUserId, sendRtpItem.getMediaServerId());
				return;
			}
			try {
				if (sendRtpItem.isTcpActive()) {
					mediaServerService.startSendRtpPassive(mediaServer, sendRtpItem, null);
				} else {
					mediaServerService.startSendRtp(mediaServer, sendRtpItem);
				}
			}catch (ControllerException e) {
				log.error("RTP推流失败: {}", e.getMessage());
				playService.startSendRtpStreamFailHand(sendRtpItem, null, callIdHeader);
			}
		}
	}

}
