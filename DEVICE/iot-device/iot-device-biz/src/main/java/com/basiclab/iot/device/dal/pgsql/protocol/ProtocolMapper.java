package com.basiclab.iot.device.dal.pgsql.protocol;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.Protocol;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Collection;
import java.util.List;

/**
 * ProtocolMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface ProtocolMapper extends BaseMapper<Protocol> {

    /**
     * 查询协议管理
     *
     * @param id 协议管理主键
     * @return 协议管理
     */
    Protocol selectProtocolById(Long id);

    /**
     * 查询协议管理列表
     *
     * @param protocol 协议管理
     * @return 协议管理集合
     */
    List<Protocol> selectProtocolList(Protocol protocol);

    /**
     * 新增协议管理
     *
     * @param protocol 协议管理
     * @return 结果
     */
    int insertProtocol(Protocol protocol);

    /**
     * 修改协议管理
     *
     * @param protocol 协议管理
     * @return 结果
     */
    int updateProtocol(Protocol protocol);

    /**
     * 批量删除协议管理
     *
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteProtocolByIds(Long[] ids);

    Protocol findOneByProductIdentificationAndProtocolTypeAndStatus(@Param("productIdentification") String productIdentification, @Param("protocolType") String protocolType, @Param("status") String status);

    List<Protocol> findAllByIdIn(@Param("idCollection") Collection<Long> idCollection);

    int updateStatusById(@Param("updatedStatus") String updatedStatus, @Param("id") Long id);

    List<Protocol> findAllByStatus(@Param("status") String status);
}
