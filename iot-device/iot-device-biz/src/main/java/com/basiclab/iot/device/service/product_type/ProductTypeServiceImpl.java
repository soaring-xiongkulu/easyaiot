package com.basiclab.iot.device.service.product_type;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.product_type.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_type.ProductTypeDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.product_type.ProductTypeMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.PRODUCT_TYPE_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 产品分类 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class ProductTypeServiceImpl implements ProductTypeService {

    @Resource
    private ProductTypeMapper productTypeMapper;

    @Override
    public Long createType(ProductTypeSaveReqVO createReqVO) {
        // 插入
        ProductTypeDO type = BeanUtils.toBean(createReqVO, ProductTypeDO.class);
        productTypeMapper.insert(type);
        // 返回
        return type.getId();
    }

    @Override
    public void updateType(ProductTypeSaveReqVO updateReqVO) {
        // 校验存在
        validateTypeExists(updateReqVO.getId());
        // 更新
        ProductTypeDO updateObj = BeanUtils.toBean(updateReqVO, ProductTypeDO.class);
        productTypeMapper.updateById(updateObj);
    }

    @Override
    public void deleteType(Long id) {
        // 校验存在
        validateTypeExists(id);
        // 删除
        productTypeMapper.deleteById(id);
    }

    private void validateTypeExists(Long id) {
        if (productTypeMapper.selectById(id) == null) {
            throw exception(PRODUCT_TYPE_NOT_EXISTS);
        }
    }

    @Override
    public ProductTypeDO getType(Long id) {
        return productTypeMapper.selectById(id);
    }

    @Override
    public PageResult<ProductTypeDO> getTypePage(ProductTypePageReqVO pageReqVO) {
        return productTypeMapper.selectPage(pageReqVO);
    }

}