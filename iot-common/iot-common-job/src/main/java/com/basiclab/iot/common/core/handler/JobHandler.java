package com.basiclab.iot.common.core.handler;

/**
 * 任务处理器
 *
 * @author 深圳市深度智核科技有限责任公司
 */
public interface JobHandler {

    /**
     * 执行任务
     *
     * @param param 参数
     * @return 结果
     * @throws Exception 异常
     */
    String execute(String param) throws Exception;

}
