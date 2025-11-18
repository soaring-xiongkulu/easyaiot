package com.basiclab.iot.device.service.protocol.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.constant.CacheConstants;
import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.service.RedisService;
import com.basiclab.iot.device.dal.pgsql.protocol.ProtocolMapper;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.Protocol;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.product.ProductService;
import com.basiclab.iot.device.service.protocol.ProtocolService;
import org.apache.commons.lang3.StringEscapeUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.Collection;
import java.util.List;

/**
 * ProtocolServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class ProtocolServiceImpl extends ServiceImpl<ProtocolMapper, Protocol> implements ProtocolService {
    @Autowired
    private DeviceService deviceService;
    @Autowired
    private ProductService productService;
    @Autowired
    private RedisService redisService;

    /**
     * 查询协议管理
     *
     * @param id 协议管理主键
     * @return 协议管理
     */
    @Override
    public Protocol selectProtocolById(Long id) {
        return baseMapper.selectProtocolById(id);
    }

    /**
     * 查询协议管理列表
     *
     * @param protocol 协议管理
     * @return 协议管理
     */
    @Override
    public List<Protocol> selectProtocolList(Protocol protocol) {
        return baseMapper.selectProtocolList(protocol);
    }

    /**
     * 新增协议管理
     *
     * @param protocol 协议管理
     * @return 结果
     */
    @Override
    public int insertProtocol(Protocol protocol) {
        return baseMapper.insertProtocol(protocol);
    }

    /**
     * 修改协议管理
     *
     * @param protocol 协议管理
     * @return 结果
     */
    @Override
    public int updateProtocol(Protocol protocol) {
        return baseMapper.updateProtocol(protocol);
    }

    /**
     * 批量删除协议管理
     *
     * @param ids 需要删除的协议管理主键
     * @return 结果
     */
    @Override
    public int deleteProtocolByIds(Long[] ids) {
        return baseMapper.deleteProtocolByIds(ids);
    }

    @Override
    public Protocol findOneByProductIdentificationAndProtocolTypeAndStatus(String productIdentification, String protocolType, String status) {
        return baseMapper.findOneByProductIdentificationAndProtocolTypeAndStatus(productIdentification, protocolType, status);
    }

    /**
     * 批量启用协议管理
     *
     * @param ids
     * @return
     */
    @Override
    public int enable(Long[] ids) {
        List<Protocol> protocolList = baseMapper.findAllByIdIn(Arrays.asList(ids));
        for (Protocol protocol : protocolList) {
            List<Device> deviceList = deviceService.findAllByProductIdentification(protocol.getProductIdentification());
            String content = StringEscapeUtils.unescapeHtml4(protocol.getContent());
            for (Device device : deviceList) {
                redisService.set(CacheConstants.DEF_DEVICE_DATA_REPORTED_AGREEMENT_SCRIPT + protocol.getProtocolType() + device.getDeviceIdentification(), content);
            }
            baseMapper.updateStatusById(Constants.ENABLE, protocol.getId());
        }
        return protocolList.size();
    }

    /**
     * 批量禁用协议管理
     *
     * @param ids
     * @return
     */
    @Override
    public int disable(Long[] ids) {
        List<Protocol> protocolList = baseMapper.findAllByIdIn(Arrays.asList(ids));
        for (Protocol protocol : protocolList) {
            List<Device> deviceList = deviceService.findAllByProductIdentification(protocol.getProductIdentification());
            for (Device device : deviceList) {
                redisService.delete(CacheConstants.DEF_DEVICE_DATA_REPORTED_AGREEMENT_SCRIPT + protocol.getProtocolType() + device.getDeviceIdentification());
            }
            baseMapper.updateStatusById(Constants.DISABLE, protocol.getId());
        }
        return protocolList.size();
    }

    @Override
    public List<Protocol> findAllByIdIn(Collection<Long> idCollection) {
        return baseMapper.findAllByIdIn(idCollection);
    }

    @Override
    public int updateStatusById(String updatedStatus, Long id) {
        return baseMapper.updateStatusById(updatedStatus, id);
    }

    /**
     * 协议脚本缓存刷新
     *
     * @return
     */
    @Override
    public int protocolScriptCacheRefresh() {
        List<Protocol> protocolList = baseMapper.selectProtocolList(Protocol.builder().build());
        for (Protocol protocol : protocolList) {
            List<Device> deviceList = deviceService.findAllByProductIdentification(protocol.getProductIdentification());
            for (Device device : deviceList) {
                if (Constants.DISABLE.equals(protocol.getStatus())) {
                    redisService.delete(CacheConstants.DEF_DEVICE_DATA_REPORTED_AGREEMENT_SCRIPT + protocol.getProtocolType() + device.getDeviceIdentification());
                } else {
                    redisService.set(CacheConstants.DEF_DEVICE_DATA_REPORTED_AGREEMENT_SCRIPT + protocol.getProtocolType() + device.getDeviceIdentification(), StringEscapeUtils.unescapeHtml4(protocol.getContent()));
                }
            }
        }
        return protocolList.size();
    }

    @Override
    public List<Protocol> findAllByStatus(String status) {
        return baseMapper.findAllByStatus(status);
    }


}
