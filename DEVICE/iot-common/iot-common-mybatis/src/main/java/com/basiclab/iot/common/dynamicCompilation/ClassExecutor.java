package com.basiclab.iot.common.dynamicCompilation;

import com.basiclab.iot.common.utils.StringUtils;

import java.io.PrintWriter;
import java.lang.reflect.Method;

/**
 * Class执行器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2025-07-04
 */
public class ClassExecutor {

    /**
     * 执行Main函数
     *
     * @param cls 待执行的类
     * @param out 错误信息输出
     * @return 是否执行成功
     */
    public boolean executeMain(Class<?> cls, PrintWriter out,String param) {
        Method method;
        try {
            //默认执行main函数
            method = cls.getMethod("main", new Class[]{String[].class});
            if (!StringUtils.isEmpty(param)) {
                method.invoke(null, (Object) new String[]{param});
            } else {
                method.invoke(null, new String[]{null});
            }
        } catch (Throwable t) {
            t.printStackTrace(out);
        }

        return false;
    }
}
