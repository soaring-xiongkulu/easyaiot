package com.basiclab.iot.device.dal.pgsql.ota;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.DmPackageVerifyPo;
import com.basiclab.iot.device.domain.ota.qo.DmVerifyPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmVerifyVo;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 测试白名单 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DmPackageVerifyMapper extends BaseMapper<DmPackageVerifyPo> {

    /**
     * 白名单分页查询（联版本包名称）
     */
    List<DmVerifyVo> getVerifyPageList(DmVerifyPageQo query);

    /**
     * 按产品统计设备数（白名单分组）
     */
    List<com.basiclab.iot.device.domain.ota.vo.DmWhiteGroupVo> countDeviceGroupByProduct();
}
