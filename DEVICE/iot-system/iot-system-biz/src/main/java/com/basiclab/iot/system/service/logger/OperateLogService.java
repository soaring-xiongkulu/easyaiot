package com.basiclab.iot.system.service.logger;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.system.api.logger.dto.OperateLogCreateReqDTO;
import com.basiclab.iot.system.api.logger.dto.OperateLogPageReqDTO;
import com.basiclab.iot.system.controller.admin.logger.vo.operatelog.OperateLogPageReqVO;
import com.basiclab.iot.system.dal.dataobject.logger.OperateLogDO;

/**
 * 操作日志 Service 接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface OperateLogService {

    /**
     * 记录操作日志
     *
     * @param createReqDTO 创建请求
     */
    void createOperateLog(OperateLogCreateReqDTO createReqDTO);

    /**
     * 获得操作日志分页列表
     *
     * @param pageReqVO 分页条件
     * @return 操作日志分页列表
     */
    PageResult<OperateLogDO> getOperateLogPage(OperateLogPageReqVO pageReqVO);

    /**
     * 获得操作日志分页列表
     *
     * @param pageReqVO 分页条件
     * @return 操作日志分页列表
     */
    PageResult<OperateLogDO> getOperateLogPage(OperateLogPageReqDTO pageReqVO);

}
