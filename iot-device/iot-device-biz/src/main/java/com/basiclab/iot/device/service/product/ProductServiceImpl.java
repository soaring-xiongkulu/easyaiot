package com.basiclab.iot.device.service.product;

import com.basiclab.iot.device.dal.mysql.product.ProductMapper;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product.vo.*;
import com.basiclab.iot.device.dal.dataobject.product.Product;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;


import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.device.enums.ErrorCodeConstants.*;

/**
 * 产品 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductServiceImpl implements ProductService {

    @Resource
    private ProductMapper productMapper;

    @Override
    public Long create(ProductSaveReqVO createReqVO) {
        // 插入
        Product productDO = BeanUtils.toBean(createReqVO, Product.class);
        productMapper.insert(productDO);
        // 返回
        return productDO.getId();
    }

    @Override
    public Product selectByProductIdentification(String productIdentification) {
        return null;
    }

    @Override
    public void update(ProductSaveReqVO updateReqVO) {
        // 校验存在
        validateExists(updateReqVO.getId());
        // 更新
        Product updateObj = BeanUtils.toBean(updateReqVO, Product.class);
        productMapper.updateById(updateObj);
    }

    @Override
    public void delete(Long id) {
        // 校验存在
        validateExists(id);
        // 删除
        productMapper.deleteById(id);
    }

    private void validateExists(Long id) {
        if (productMapper.selectById(id) == null) {
            throw exception(PRODUCT_NOT_EXISTS);
        }
    }

    @Override
    public Product get(Long id) {
        return productMapper.selectById(id);
    }

    @Override
    public PageResult<Product> getPage(ProductPageReqVO pageReqVO) {
        return productMapper.selectPage(pageReqVO);
    }

}