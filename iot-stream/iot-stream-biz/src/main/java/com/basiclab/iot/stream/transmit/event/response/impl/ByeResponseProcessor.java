package com.basiclab.iot.stream.transmit.event.response.impl;

import com.basiclab.iot.stream.transmit.ISIPProcessorObserver;
import com.basiclab.iot.stream.transmit.SIPProcessorObserver;
import com.basiclab.iot.stream.transmit.event.response.SIPResponseProcessorAbstract;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.sip.ResponseEvent;

/**    
 * @description: BYE请求响应器
 * @author: swwheihei
 * @date:   2020年5月3日 下午5:32:05     
 */
@Component
public class ByeResponseProcessor extends SIPResponseProcessorAbstract {

	private final String method = "BYE";

	@Autowired
	private ISIPProcessorObserver sipProcessorObserver;

	@Override
	public void afterPropertiesSet() throws Exception {
		// 添加消息处理的订阅
		sipProcessorObserver.addResponseProcessor(method, this);
	}
	/**
	 * 处理BYE响应
	 * 
	 * @param evt
	 */
	@Override
	public void process(ResponseEvent evt) {
		// TODO Auto-generated method stub
	}


}
