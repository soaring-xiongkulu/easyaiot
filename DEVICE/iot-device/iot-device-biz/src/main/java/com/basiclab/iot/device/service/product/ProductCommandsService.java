package com.basiclab.iot.device.service.product;

import com.baomidou.mybatisplus.extension.service.IService;
import com.basiclab.iot.device.domain.device.vo.ProductCommands;

import java.util.List;

/**
 * ProductCommandsService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ProductCommandsService extends IService<ProductCommands> {

    /**
     * 查询产品模型设备服务命令
     *
     * @param id 产品模型设备服务命令主键
     * @return 产品模型设备服务命令
     */
    ProductCommands selectProductCommandsById(Long id);

    /**
     * 查询产品模型设备服务命令列表
     *
     * @param productCommands 产品模型设备服务命令
     * @return 产品模型设备服务命令集合
     */
    List<ProductCommands> selectProductCommandsList(ProductCommands productCommands);

    /**
     * 新增产品模型设备服务命令
     *
     * @param productCommands 产品模型设备服务命令
     * @return 结果
     */
    int insertProductCommands(ProductCommands productCommands);

    /**
     * 修改产品模型设备服务命令
     *
     * @param productCommands 产品模型设备服务命令
     * @return 结果
     */
    int updateProductCommands(ProductCommands productCommands);

    /**
     * 批量删除产品模型设备服务命令
     *
     * @param ids 需要删除的产品模型设备服务命令主键集合
     * @return 结果
     */
    int deleteProductCommandsByIds(Long[] ids);

    List<ProductCommands> selectProductCommandsByIdList(List<Long> commandIdList);

    List<ProductCommands> selectProductCommandsByServiceIdList(List<Long> serviceIdList);


}
