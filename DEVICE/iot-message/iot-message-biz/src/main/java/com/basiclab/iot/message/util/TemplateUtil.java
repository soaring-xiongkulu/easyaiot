package com.basiclab.iot.message.util;

import cn.hutool.core.date.DateUtil;
import com.basiclab.iot.message.mapper.TWxMpUserMapper;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.io.StringWriter;
import java.util.Date;

/**
 * <pre>
 * 模板工具
 * </pre>
 *
 * @author <a href="https://github.com/rememberber">RememBerBer</a>
 * @since 2019/1/5.
 */
@Component
public class TemplateUtil {

    @Autowired
    private TWxMpUserMapper tWxMpUserMapper;

    private static VelocityEngine velocityEngine;

    static {
        velocityEngine = new VelocityEngine();
        velocityEngine.init();
    }

    public static String evaluate(String content, VelocityContext velocityContext) {

        if (content.contains("NICK_NAME")) {
            String nickName = "";
            velocityContext.put("NICK_NAME", nickName);
        }

        velocityContext.put("ENTER", "\n");
        Date now = new Date();
        velocityContext.put("DATE", DateUtil.today());
        velocityContext.put("TIME", DateUtil.formatTime(now));
        velocityContext.put("DATE_TIME", DateUtil.formatDateTime(now));

        StringWriter writer = new StringWriter();
        velocityEngine.evaluate(velocityContext, writer, "", content);

        return writer.toString();
    }
}
