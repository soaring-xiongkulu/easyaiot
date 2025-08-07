package com.basiclab.iot.stream.transmit.event.response.impl;

import com.basiclab.iot.stream.transmit.ISIPProcessorObserver;
import com.basiclab.iot.stream.transmit.SIPProcessorObserver;
import com.basiclab.iot.stream.transmit.event.response.SIPResponseProcessorAbstract;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.sip.ResponseEvent;

/**    
 * @description: CANCEL响应处理器
 * @author: panlinlin
 * @date:   2021年11月5日 16:35
 */
@Component
public class CancelResponseProcessor extends SIPResponseProcessorAbstract {

	private final String method = "CANCEL";

	@Autowired
	private ISIPProcessorObserver sipProcessorObserver;

	@Override
	public void afterPropertiesSet() throws Exception {
		// 添加消息处理的订阅
		sipProcessorObserver.addResponseProcessor(method, this);
	}
	/**   
	 * 处理CANCEL响应
	 *  
	 * @param evt
	 */
	@Override
	public void process(ResponseEvent evt) {
		// TODO Auto-generated method stub
		
	}

}
