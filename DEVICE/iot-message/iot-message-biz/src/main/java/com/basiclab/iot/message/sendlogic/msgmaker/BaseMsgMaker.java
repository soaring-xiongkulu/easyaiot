package com.basiclab.iot.message.sendlogic.msgmaker;


import com.basiclab.iot.message.sendlogic.PushControl;
import org.apache.velocity.VelocityContext;

/**
 * 消息加工器基类
 */
public class BaseMsgMaker {
    /**
     * 获取模板引擎上下文
     *
     * @param msgData 消息数据
     * @return VelocityContext 模板引擎上下文
     */
    VelocityContext getVelocityContext(String[] msgData) {
        VelocityContext velocityContext = new VelocityContext();
        for (int i = 0; i < msgData.length; i++) {
            velocityContext.put(PushControl.TEMPLATE_VAR_PREFIX + i, msgData[i]);
        }
        return velocityContext;
    }
}
