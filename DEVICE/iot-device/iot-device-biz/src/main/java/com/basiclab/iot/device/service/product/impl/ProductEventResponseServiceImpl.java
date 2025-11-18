package com.basiclab.iot.device.service.product.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.device.domain.device.vo.ProductEventResponse;
import com.basiclab.iot.device.dal.pgsql.product.ProductEventResponseMapper;
import com.basiclab.iot.device.service.product.ProductEventResponseService;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * ProductEventResponseServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
public class ProductEventResponseServiceImpl extends ServiceImpl<ProductEventResponseMapper, ProductEventResponse> implements ProductEventResponseService {

    @Override
    public ProductEventResponse queryById(Long id) {
        return baseMapper.queryById(id);
    }

    @Override
    public List<ProductEventResponse> selectList(ProductEventResponse productEventResponse) {
        return baseMapper.selectList(productEventResponse);
    }

    @Override
    public Long count(ProductEventResponse productEventResponse) {
        return baseMapper.count(productEventResponse);
    }

    @Override
    public int insert(ProductEventResponse productEventResponse) {
        return baseMapper.insert(productEventResponse);
    }

    @Override
    public int insertBatch(List<ProductEventResponse> entities) {
        return baseMapper.insertBatch(entities);
    }

    @Override
    public int insertOrUpdateBatch(List<ProductEventResponse> entities) {
        return baseMapper.insertOrUpdateBatch(entities);
    }

    @Override
    public int update(ProductEventResponse productEventResponse) {
        return baseMapper.update(productEventResponse);
    }

    @Override
    public int deleteByIds(Long[] ids) {
        return baseMapper.deleteByIds(ids);
    }
}

