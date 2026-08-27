package com.basiclab.iot.device.service.ota;

import com.basiclab.iot.device.domain.ota.oo.DmOtaCheckOo;
import com.basiclab.iot.device.domain.ota.oo.DmOtaReportOo;
import com.basiclab.iot.device.domain.ota.vo.OtaUpgradeItemVo;

import java.util.List;

/**
 * 设备侧统一 OTA 出入口
 * <p>
 * 4 种包类型（固件/软件/APP/PC）共用同一套检测与上报接口：
 * 一次 check 携带全部类型的当前版本，返回全部待升级项；一次 report 上报任意的升级阶段事件。
 * <p>
 * 升级采用拉取模型：由设备/APP 主动发起检测，平台仅做应答，不做主动下行推送。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DmOtaService {

    /**
     * 设备升级检测（统一出入口）
     * <p>
     * 候选来源：已发布包（正式通道，含灰度命中）+ 测试白名单命中的测试中包（测试通道）；
     * 按产品适用性、版本新旧过滤；存在关键版本（keyVersionFlag=1）时取最小关键版本强制升级，
     * 否则取最大版本。
     *
     * @param oo 检测请求（携带设备标识与各类型当前版本）
     * @return 待升级项列表（按类型最多一项）
     */
    List<OtaUpgradeItemVo> check(DmOtaCheckOo oo);

    /**
     * 设备升级进度/结果上报（统一出入口）
     * <p>
     * 幂等 upsert：同一设备同一类型同一目标版本同一阶段只保留一条记录。
     *
     * @param oo 上报请求
     */
    void report(DmOtaReportOo oo);
}
