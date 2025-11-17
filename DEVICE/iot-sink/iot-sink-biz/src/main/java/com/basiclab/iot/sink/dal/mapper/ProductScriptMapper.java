package com.basiclab.iot.sink.dal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.sink.dal.dataobject.ProductScriptDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 产品脚本 Mapper
 *
 * @author 翱翔的雄库鲁
 */
@Mapper
public interface ProductScriptMapper extends BaseMapper<ProductScriptDO> {

    /**
     * 根据产品标识查询脚本
     *
     * @param productIdentification 产品标识
     * @return 产品脚本
     */
    ProductScriptDO selectByProductIdentification(@Param("productIdentification") String productIdentification);

    /**
     * 查询所有启用的脚本
     *
     * @return 启用的脚本列表
     */
    List<ProductScriptDO> selectAllEnabled();

    /**
     * 根据产品ID查询脚本
     *
     * @param productId 产品ID
     * @return 产品脚本
     */
    ProductScriptDO selectByProductId(@Param("productId") Long productId);
}

