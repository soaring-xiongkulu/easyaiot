package com.basiclab.iot.stream.controller;

import com.basiclab.iot.stream.common.InviteInfo;
import com.basiclab.iot.stream.common.InviteSessionType;
import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.config.exception.ControllerException;
import com.basiclab.iot.stream.config.exception.ServiceException;
import com.basiclab.iot.stream.config.security.JwtUtils;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.DeviceChannel;
import com.basiclab.iot.stream.service.IDeviceChannelService;
import com.basiclab.iot.stream.service.IDeviceService;
import com.basiclab.iot.stream.service.IInviteStreamService;
import com.basiclab.iot.stream.service.IPlayService;
import com.basiclab.iot.stream.transmit.callback.DeferredResultHolder;
import com.basiclab.iot.stream.transmit.callback.RequestMessage;
import com.basiclab.iot.stream.transmit.cmd.impl.SIPCommander;
import com.basiclab.iot.stream.service.bean.InviteErrorCode;
import com.basiclab.iot.stream.vmanager.bean.ErrorCode;
import com.basiclab.iot.stream.vmanager.bean.StreamContent;
import com.basiclab.iot.stream.vmanager.bean.WVPResult;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.util.ObjectUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.request.async.DeferredResult;

import javax.servlet.http.HttpServletRequest;
import javax.sip.InvalidArgumentException;
import javax.sip.SipException;
import java.net.MalformedURLException;
import java.net.URL;
import java.text.ParseException;
import java.util.UUID;

/**
 * @author lin
 */
@Tag(name = "视频回放")
@Slf4j
@RestController
@RequestMapping("/api/playback")
public class PlaybackController {

	@Autowired
	private SIPCommander cmder;

	@Autowired
	private IInviteStreamService inviteStreamService;

	@Autowired
	private IPlayService playService;

	@Autowired
	private DeferredResultHolder resultHolder;

	@Autowired
	private UserSetting userSetting;

	@Autowired
	private IDeviceService deviceService;

	@Autowired
	private IDeviceChannelService channelService;

	@Operation(summary = "开始视频回放", security = @SecurityRequirement(name = JwtUtils.HEADER))
	@Parameter(name = "deviceId", description = "设备国标编号", required = true)
	@Parameter(name = "channelId", description = "通道国标编号", required = true)
	@Parameter(name = "startTime", description = "开始时间", required = true)
	@Parameter(name = "endTime", description = "结束时间", required = true)
	@GetMapping("/start/{deviceId}/{channelId}")
	public DeferredResult<WVPResult<StreamContent>> start(HttpServletRequest request, @PathVariable String deviceId, @PathVariable String channelId,
														  String startTime, String endTime) {

		if (log.isDebugEnabled()) {
			log.debug(String.format("设备回放 API调用，deviceId：%s ，channelId：%s", deviceId, channelId));
		}

		String uuid = UUID.randomUUID().toString();
		String key = DeferredResultHolder.CALLBACK_CMD_PLAYBACK + deviceId + channelId;
		DeferredResult<WVPResult<StreamContent>> result = new DeferredResult<>(userSetting.getPlayTimeout().longValue());
		resultHolder.put(key, uuid, result);

		RequestMessage requestMessage = new RequestMessage();
		requestMessage.setKey(key);
		requestMessage.setId(uuid);
		Device device = deviceService.getDeviceByDeviceId(deviceId);
		if (device == null) {
			log.warn("[录像回放] 未找到设备 deviceId: {},channelId:{}", deviceId, channelId);
			throw new ControllerException(ErrorCode.ERROR100.getCode(), "未找到设备：" + deviceId);
		}

		DeviceChannel channel = channelService.getOne(deviceId, channelId);
		if (channel == null) {
			log.warn("[录像回放] 未找到通道 deviceId: {},channelId:{}", deviceId, channelId);
			throw new ControllerException(ErrorCode.ERROR100.getCode(), "未找到通道：" + channelId);
		}
		playService.playBack(device, channel, startTime, endTime,
				(code, msg, data)->{

					WVPResult<StreamContent> wvpResult = new WVPResult<>();
					if (code == InviteErrorCode.SUCCESS.getCode()) {
						wvpResult.setCode(ErrorCode.SUCCESS.getCode());
						wvpResult.setMsg(ErrorCode.SUCCESS.getMsg());

						if (data != null) {
							StreamInfo streamInfo = (StreamInfo)data;
							if (userSetting.getUseSourceIpAsStreamIp()) {
								streamInfo=streamInfo.clone();//深拷贝
								String host;
								try {
									URL url=new URL(request.getRequestURL().toString());
									host=url.getHost();
								} catch (MalformedURLException e) {
									host=request.getLocalAddr();
								}
								streamInfo.changeStreamIp(host);
							}
							wvpResult.setData(new StreamContent(streamInfo));
						}
					}else {
						wvpResult.setCode(code);
						wvpResult.setMsg(msg);
					}
					requestMessage.setData(wvpResult);
					resultHolder.invokeResult(requestMessage);
				});

		return result;
	}


	@Operation(summary = "停止视频回放", security = @SecurityRequirement(name = JwtUtils.HEADER))
	@Parameter(name = "deviceId", description = "设备国标编号", required = true)
	@Parameter(name = "channelId", description = "通道国标编号", required = true)
	@Parameter(name = "stream", description = "流ID", required = true)
	@GetMapping("/stop/{deviceId}/{channelId}/{stream}")
	public void playStop(
			@PathVariable String deviceId,
			@PathVariable String channelId,
			@PathVariable String stream) {
		if (ObjectUtils.isEmpty(deviceId) || ObjectUtils.isEmpty(channelId) || ObjectUtils.isEmpty(stream)) {
			throw new ControllerException(ErrorCode.ERROR400);
		}
		Device device = deviceService.getDeviceByDeviceId(deviceId);
		if (device == null) {
			throw new ControllerException(ErrorCode.ERROR400.getCode(), "设备：" + deviceId + " 未找到");
		}
		DeviceChannel deviceChannel = channelService.getOneForSource(deviceId, channelId);
		if (deviceChannel == null) {
			throw new ControllerException(ErrorCode.ERROR400.getCode(), "通道：" + channelId + " 未找到");
		}
		playService.stop(InviteSessionType.PLAYBACK, device, deviceChannel, stream);
	}


	@Operation(summary = "回放暂停", security = @SecurityRequirement(name = JwtUtils.HEADER))
	@Parameter(name = "streamId", description = "回放流ID", required = true)
	@GetMapping("/pause/{streamId}")
	public void playPause(@PathVariable String streamId) {
		log.info("[回放暂停] streamId: {}", streamId);
		try {
			playService.pauseRtp(streamId);
		} catch (ServiceException e) {
			throw new ControllerException(ErrorCode.ERROR400.getCode(), e.getMessage());
		} catch (InvalidArgumentException | ParseException | SipException e) {
			throw new ControllerException(ErrorCode.ERROR100.getCode(), e.getMessage());
		}
	}


	@Operation(summary = "回放恢复", security = @SecurityRequirement(name = JwtUtils.HEADER))
	@Parameter(name = "streamId", description = "回放流ID", required = true)
	@GetMapping("/resume/{streamId}")
	public void playResume(@PathVariable String streamId) {
		log.info("playResume: "+streamId);
		try {
			playService.resumeRtp(streamId);
		} catch (ServiceException e) {
			throw new ControllerException(ErrorCode.ERROR400.getCode(), e.getMessage());
		} catch (InvalidArgumentException | ParseException | SipException e) {
			throw new ControllerException(ErrorCode.ERROR100.getCode(), e.getMessage());
		}
	}


	@Operation(summary = "回放拖动播放", security = @SecurityRequirement(name = JwtUtils.HEADER))
	@Parameter(name = "streamId", description = "回放流ID", required = true)
	@Parameter(name = "seekTime", description = "拖动偏移量，单位s", required = true)
	@GetMapping("/seek/{streamId}/{seekTime}")
	public void playSeek(@PathVariable String streamId, @PathVariable long seekTime) {
		log.info("playSeek: "+streamId+", "+seekTime);
		InviteInfo inviteInfo = inviteStreamService.getInviteInfoByStream(InviteSessionType.PLAYBACK, streamId);

		if (null == inviteInfo || inviteInfo.getStreamInfo() == null) {
			log.warn("streamId不存在!");
			throw new ControllerException(ErrorCode.ERROR400.getCode(), "streamId不存在");
		}
		Device device = deviceService.getDeviceByDeviceId(inviteInfo.getDeviceId());
		DeviceChannel channel = channelService.getOneById(inviteInfo.getChannelId());
		try {
			cmder.playSeekCmd(device, channel, inviteInfo.getStreamInfo(), seekTime);
		} catch (InvalidArgumentException | ParseException | SipException e) {
			throw new ControllerException(ErrorCode.ERROR100.getCode(), e.getMessage());
		}
	}

	@Operation(summary = "回放倍速播放", security = @SecurityRequirement(name = JwtUtils.HEADER))
	@Parameter(name = "streamId", description = "回放流ID", required = true)
	@Parameter(name = "speed", description = "倍速0.25 0.5 1、2、4、8", required = true)
	@GetMapping("/speed/{streamId}/{speed}")
	public void playSpeed(@PathVariable String streamId, @PathVariable Double speed) {
		log.info("playSpeed: "+streamId+", "+speed);
		InviteInfo inviteInfo = inviteStreamService.getInviteInfoByStream(InviteSessionType.PLAYBACK, streamId);

		if (null == inviteInfo || inviteInfo.getStreamInfo() == null) {
			log.warn("streamId不存在!");
			throw new ControllerException(ErrorCode.ERROR400.getCode(), "streamId不存在");
		}
		Device device = deviceService.getDeviceByDeviceId(inviteInfo.getDeviceId());
		DeviceChannel channel = channelService.getOneById(inviteInfo.getChannelId());
		try {
			cmder.playSpeedCmd(device, channel, inviteInfo.getStreamInfo(), speed);
		} catch (InvalidArgumentException | ParseException | SipException e) {
			throw new ControllerException(ErrorCode.ERROR100.getCode(), e.getMessage());
		}
	}
}
