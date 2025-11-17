package com.basiclab.iot.sink.service.product.script;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.sink.dal.dataobject.ProductScriptDO;
import com.basiclab.iot.sink.dal.mapper.ProductScriptMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

/**
 * 产品脚本 Service 实现类
 *
 * @author 翱翔的雄库鲁
 */
@Service
@Slf4j
public class ProductScriptServiceImpl implements ProductScriptService {

    @Resource
    private ProductScriptMapper productScriptMapper;

    @Override
    public ProductScriptDO getScriptByProductIdentification(String productIdentification) {
        ProductScriptDO script = productScriptMapper.selectByProductIdentification(productIdentification);
        if (script == null || !Boolean.TRUE.equals(script.getScriptEnabled())) {
            return null;
        }
        return script;
    }

    @Override
    public ProductScriptDO getScriptByProductId(Long productId) {
        ProductScriptDO script = productScriptMapper.selectByProductId(productId);
        if (script == null || !Boolean.TRUE.equals(script.getScriptEnabled())) {
            return null;
        }
        return script;
    }

    @Override
    public List<ProductScriptDO> getAllEnabledScripts() {
        return productScriptMapper.selectAllEnabled();
    }

    @Override
    public void saveOrUpdate(ProductScriptDO script) {
        if (script.getId() == null) {
            // 新增
            productScriptMapper.insert(script);
            log.info("[saveOrUpdate][新增产品脚本，产品ID: {}, 产品标识: {}]", script.getProductId(), script.getProductIdentification());
        } else {
            // 更新
            productScriptMapper.updateById(script);
            log.info("[saveOrUpdate][更新产品脚本，脚本ID: {}, 产品ID: {}, 产品标识: {}]", 
                    script.getId(), script.getProductId(), script.getProductIdentification());
        }
    }

    @Override
    public void deleteByProductId(Long productId) {
        LambdaQueryWrapper<ProductScriptDO> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ProductScriptDO::getProductId, productId);
        productScriptMapper.delete(wrapper);
        log.info("[deleteByProductId][删除产品脚本，产品ID: {}]", productId);
    }
}

