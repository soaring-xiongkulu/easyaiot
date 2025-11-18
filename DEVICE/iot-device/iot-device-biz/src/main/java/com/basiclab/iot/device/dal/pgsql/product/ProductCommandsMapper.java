package com.basiclab.iot.device.dal.pgsql.product;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.domain.device.vo.ProductCommands;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * ProductCommandsMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface ProductCommandsMapper extends BaseMapper<ProductCommands> {

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
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
    int deleteProductCommandsByIds(Long[] ids);

    List<ProductCommands> selectProductCommandsByIdList(@Param("commandIdList") List<Long> commandIdList);

    List<ProductCommands> selectProductCommandsByServiceIdList(@Param("serviceIdList") List<Long> serviceIdList);
}
