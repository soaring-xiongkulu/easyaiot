package com.basiclab.iot.sink.service.product.script;

import com.basiclab.iot.sink.dal.dataobject.ProductScriptDO;

import java.util.List;

/**
 * 产品脚本 Service 接口
 *
 * @author 翱翔的雄库鲁
 */
public interface ProductScriptService {

    /**
     * 根据产品标识获取脚本
     *
     * @param productIdentification 产品标识
     * @return 产品脚本，如果不存在或未启用则返回 null
     */
    ProductScriptDO getScriptByProductIdentification(String productIdentification);

    /**
     * 根据产品ID获取脚本
     *
     * @param productId 产品ID
     * @return 产品脚本，如果不存在或未启用则返回 null
     */
    ProductScriptDO getScriptByProductId(Long productId);

    /**
     * 获取所有启用的脚本
     *
     * @return 启用的脚本列表
     */
    List<ProductScriptDO> getAllEnabledScripts();

    /**
     * 保存或更新脚本
     *
     * @param script 脚本信息
     */
    void saveOrUpdate(ProductScriptDO script);

    /**
     * 删除脚本
     *
     * @param productId 产品ID
     */
    void deleteByProductId(Long productId);
}

