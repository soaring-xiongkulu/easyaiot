package com.basiclab.iot.device.service.product.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.device.dal.pgsql.product.ProductEventMapper;
import com.basiclab.iot.device.domain.device.vo.ProductEvent;
import com.basiclab.iot.device.service.product.ProductEventService;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * ProductEventServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class ProductEventServiceImpl extends ServiceImpl<ProductEventMapper, ProductEvent> implements ProductEventService {

    @Override
    public ProductEvent queryById(Long id) {
        return baseMapper.queryById(id);
    }

    @Override
    public List<ProductEvent> selectList(ProductEvent productEvent) {
        return baseMapper.selectList(productEvent);
    }

    @Override
    public Long count(ProductEvent productEvent) {
        return baseMapper.count(productEvent);
    }

    @Override
    public int insert(ProductEvent productEvent) {
        return baseMapper.insert(productEvent);
    }

    @Override
    public int insertBatch(List<ProductEvent> entities) {
        return baseMapper.insertBatch(entities);
    }

    @Override
    public int insertOrUpdateBatch(List<ProductEvent> entities) {
        return baseMapper.insertOrUpdateBatch(entities);
    }

    @Override
    public int update(ProductEvent productEvent) {
        return baseMapper.update(productEvent);
    }

    @Override
    public int deleteByIds(Long[] ids) {
        return baseMapper.deleteById(ids);
    }
}

