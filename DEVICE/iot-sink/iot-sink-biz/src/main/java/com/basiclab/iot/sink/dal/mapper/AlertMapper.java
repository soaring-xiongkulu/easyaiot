package com.basiclab.iot.sink.dal.mapper;

import com.baomidou.dynamic.datasource.annotation.DS;
import com.basiclab.iot.sink.dal.dataobject.AlertDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Component;

/**
 * Alert Mapper接口
 * 使用@DS("video")注解切换到VIDEO数据库
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
@Component
@DS("video")
public interface AlertMapper {

    /**
     * 插入告警记录
     *
     * @param alert 告警实体
     * @return 插入的行数
     */
    int insert(AlertDO alert);

    /**
     * 根据ID查询告警记录
     *
     * @param id 告警ID
     * @return 告警实体
     */
    AlertDO selectById(@Param("id") Integer id);

    /**
     * 更新告警记录的图片路径
     *
     * @param id 告警ID
     * @param imagePath 图片路径
     * @return 更新的行数
     */
    int updateImagePath(@Param("id") Integer id, @Param("imagePath") String imagePath);
}

