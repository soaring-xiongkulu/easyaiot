package com.basiclab.iot.device.service.protocol;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.protocol.vo.*;
import com.basiclab.iot.device.dal.dataobject.protocol.ProtocolDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 协议信息 Service 接口
 *
 * @author BasicLab
 */
public interface ProtocolService {

    /**
     * 创建协议信息
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long create(@Valid ProtocolSaveReqVO createReqVO);

    /**
     * 更新协议信息
     *
     * @param updateReqVO 更新信息
     */
    void update(@Valid ProtocolSaveReqVO updateReqVO);

    /**
     * 删除协议信息
     *
     * @param id 编号
     */
    void delete(Long id);

    /**
     * 获得协议信息
     *
     * @param id 编号
     * @return 协议信息
     */
    ProtocolDO get(Long id);

    /**
     * 获得协议信息分页
     *
     * @param pageReqVO 分页查询
     * @return 协议信息分页
     */
    PageResult<ProtocolDO> getPage(ProtocolPageReqVO pageReqVO);

}