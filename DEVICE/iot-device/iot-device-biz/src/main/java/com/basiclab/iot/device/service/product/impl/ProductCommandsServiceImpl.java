package com.basiclab.iot.device.service.product.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.device.domain.device.vo.ProductCommands;
import com.basiclab.iot.device.dal.pgsql.product.ProductCommandsMapper;
import com.basiclab.iot.device.service.product.ProductCommandsService;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * ProductCommandsServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class ProductCommandsServiceImpl extends ServiceImpl<ProductCommandsMapper, ProductCommands> implements ProductCommandsService {

    /**
     * 查询产品模型设备服务命令
     *
     * @param id 产品模型设备服务命令主键
     * @return 产品模型设备服务命令
     */
    @Override
    public ProductCommands selectProductCommandsById(Long id) {
        return baseMapper.selectProductCommandsById(id);
    }

    /**
     * 查询产品模型设备服务命令列表
     *
     * @param productCommands 产品模型设备服务命令
     * @return 产品模型设备服务命令
     */
    @Override
    public List<ProductCommands> selectProductCommandsList(ProductCommands productCommands) {
        return baseMapper.selectProductCommandsList(productCommands);
    }

    /**
     * 新增产品模型设备服务命令
     *
     * @param productCommands 产品模型设备服务命令
     * @return 结果
     */
    @Override
    public int insertProductCommands(ProductCommands productCommands) {
        return baseMapper.insertProductCommands(productCommands);
    }

    /**
     * 修改产品模型设备服务命令
     *
     * @param productCommands 产品模型设备服务命令
     * @return 结果
     */
    @Override
    public int updateProductCommands(ProductCommands productCommands) {
        return baseMapper.updateProductCommands(productCommands);
    }

    /**
     * 批量删除产品模型设备服务命令
     *
     * @param ids 需要删除的产品模型设备服务命令主键
     * @return 结果
     */
    @Override
    public int deleteProductCommandsByIds(Long[] ids) {
        return baseMapper.deleteProductCommandsByIds(ids);
    }

    @Override
    public List<ProductCommands> selectProductCommandsByIdList(List<Long> commandIdList){
        return baseMapper.selectProductCommandsByIdList(commandIdList);
    }

    @Override
    public List<ProductCommands> selectProductCommandsByServiceIdList(List<Long> serviceIdList) {
        return baseMapper.selectProductCommandsByServiceIdList(serviceIdList);
    }
}
