package com.basiclab.iot.device.dal.pgsql.ota;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.DmUpgradeRecordPo;
import com.basiclab.iot.device.domain.ota.qo.DmUpgradeRecordPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmUpgradeRecordVo;
import com.basiclab.iot.device.domain.ota.vo.DmUpgradeStatsVo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 升级记录 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DmUpgradeRecordMapper extends BaseMapper<DmUpgradeRecordPo> {

    /**
     * 升级记录分页查询（联版本包名称）
     */
    List<DmUpgradeRecordVo> getUpgradeRecordPageList(DmUpgradeRecordPageQo query);

    /**
     * 漏斗统计（各阶段去重设备数）
     */
    List<DmUpgradeStatsVo.DmFunnelItemVo> countFunnelByPhase(@Param("pkgId") Long pkgId, @Param("startTime") java.time.LocalDateTime startTime);

    /**
     * 命中升级设备数（去重）
     */
    Long countDistinctDeviceByPhase(@Param("pkgId") Long pkgId, @Param("phase") Integer phase,
                                    @Param("startTime") java.time.LocalDateTime startTime);

    /**
     * 安装结果成功记录数
     */
    Long countInstallSuccess(@Param("pkgId") Long pkgId, @Param("startTime") java.time.LocalDateTime startTime);

    /**
     * 安装结果记录数
     */
    Long countInstallTotal(@Param("pkgId") Long pkgId, @Param("startTime") java.time.LocalDateTime startTime);

    /**
     * Top 错误码统计
     */
    List<DmUpgradeStatsVo.DmErrorTopVo> countErrorTops(@Param("pkgId") Long pkgId,
                                                       @Param("startTime") java.time.LocalDateTime startTime);
}
