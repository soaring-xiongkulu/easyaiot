package com.basiclab.iot.device.dal.pgsql.apppanel;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.AppPanelTemplateDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * AppPanelTemplateMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface AppPanelTemplateMapper extends BaseMapper<AppPanelTemplateDO> {

    /**
     * 按模板编码查询
     *
     * @param templateCode 模板编码
     * @return 模板
     */
    AppPanelTemplateDO selectByTemplateCode(@Param("templateCode") String templateCode);

    /**
     * 查询产品已发布的模板（同产品多个已发布时取最近更新的一条）
     *
     * @param productIdentification 产品标识
     * @return 已发布模板
     */
    AppPanelTemplateDO selectPublishedByProductIdentification(@Param("productIdentification") String productIdentification);
}
