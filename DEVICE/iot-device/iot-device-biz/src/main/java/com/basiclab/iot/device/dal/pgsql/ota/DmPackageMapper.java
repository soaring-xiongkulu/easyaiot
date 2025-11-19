package com.basiclab.iot.device.dal.pgsql.ota;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.DmPackagePo;
import com.basiclab.iot.device.domain.ota.oo.DmDeviceDetectOo;
import com.basiclab.iot.device.domain.ota.qo.DmPackagePageQo;
import com.basiclab.iot.device.domain.ota.vo.DmPackagePageVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackageVersionVo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@Mapper
public interface DmPackageMapper extends BaseMapper<DmPackagePo> {

    /**
     * 根据条件获取版本包列表
     *
     * @param packagePageQo
     * @return
     * @author 翱翔的雄库鲁
     * @email andywebjava@163.com
     * @wechat EasyAIoT2025
     * @date 2025-05-27
     */
    List<DmPackagePageVo> getPackageListByCondition(DmPackagePageQo packagePageQo);

    /**
     * 根据设备校验名单获取软件包
     *
     * @param dmDeviceDetectOo
     * @return
     * @author 翱翔的雄库鲁
     * @email andywebjava@163.com
     * @wechat EasyAIoT2025
     * @date 2025-05-28
     */
    List<DmPackagePo> getPackageByVerifyList(DmDeviceDetectOo dmDeviceDetectOo);

    /**
     * 获取已发布版本包列表
     *
     * @param dmDeviceDetectOo
     * @return
     * @author 翱翔的雄库鲁
     * @email andywebjava@163.com
     * @wechat EasyAIoT2025
     * @date 202/5/28
     */
    List<DmPackagePo> getPublishedPackageList(DmDeviceDetectOo dmDeviceDetectOo);


    /**
     * 根据包类型获取版本列表
     *
     * @param type
     * @return
     * @author 翱翔的雄库鲁
     * @email andywebjava@163.com
     * @wechat EasyAIoT2025
     * @date 2025-05-28
     */
    List<DmPackageVersionVo> getVersionListByType(@Param("type") Integer type);
}
