package com.basiclab.iot.device.service.ota.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.device.dal.dataobject.DmPackageGrayScopePo;
import com.basiclab.iot.device.dal.dataobject.DmPackagePo;
import com.basiclab.iot.device.dal.dataobject.DmPackageVerifyPo;
import com.basiclab.iot.device.dal.dataobject.DmUpgradeRecordPo;
import com.basiclab.iot.device.dal.pgsql.device.DeviceMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageGrayScopeMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageVerifyMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmUpgradeRecordMapper;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.ota.oo.DmOtaCheckOo;
import com.basiclab.iot.device.domain.ota.oo.DmOtaReportOo;
import com.basiclab.iot.device.domain.ota.oo.DmOtaVersionOo;
import com.basiclab.iot.device.domain.ota.vo.OtaUpgradeItemVo;
import com.basiclab.iot.device.enums.ota.DmGrayScopeType;
import com.basiclab.iot.device.enums.ota.DmPackageGrayLadder;
import com.basiclab.iot.device.enums.ota.DmPackageStatus;
import com.basiclab.iot.device.enums.ota.DmPackageType;
import com.basiclab.iot.device.enums.ota.DmPackageUpgradePhase;
import com.basiclab.iot.device.enums.ota.DmUpgradeChannel;
import com.basiclab.iot.device.service.ota.DmOtaService;
import com.basiclab.iot.device.service.ota.util.OtaVersionUtils;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 设备侧统一 OTA 出入口实现
 * <p>
 * 升级检测采用拉取模型：由设备/APP 通过 HTTP 主动发起检测，平台仅做应答，不做主动下行推送。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Slf4j
public class DmOtaServiceImpl extends ServiceImpl<DmPackageMapper, DmPackagePo> implements DmOtaService {

    @Resource
    private DmPackageVerifyMapper dmPackageVerifyMapper;

    @Resource
    private DmPackageGrayScopeMapper dmPackageGrayScopeMapper;

    @Resource
    private DmUpgradeRecordMapper dmUpgradeRecordMapper;

    @Resource
    private DeviceMapper deviceMapper;

    @Override
    public List<OtaUpgradeItemVo> check(DmOtaCheckOo oo) {
        if (StringUtils.isBlank(oo.getDeviceIdentification())) {
            throw new ServiceException("设备标识不能为空");
        }
        List<OtaUpgradeItemVo> result = new ArrayList<>();
        //待检测类型：请求未携带时按全部 4 种类型检测
        List<DmOtaVersionOo> versions = oo.getVersions();
        if (ObjectUtils.isEmpty(versions)) {
            versions = new ArrayList<>();
            for (DmPackageType type : DmPackageType.values()) {
                DmOtaVersionOo v = new DmOtaVersionOo();
                v.setType(type.getCode());
                v.setVersion(StringUtils.defaultString(oo.getDeviceVersion()));
                versions.add(v);
            }
        }
        for (DmOtaVersionOo version : versions) {
            OtaUpgradeItemVo item = checkByType(oo, version);
            if (item != null) {
                result.add(item);
            }
        }
        return result;
    }

    /**
     * 单个类型的升级检测
     * <p>
     * 通道判定：设备命中测试白名单（存在测试中绑定包）时仅走测试通道；
     * 否则走正式通道，按灰度范围匹配已发布包。
     */
    private OtaUpgradeItemVo checkByType(DmOtaCheckOo oo, DmOtaVersionOo current) {
        Integer type = current.getType();
        if (!DmPackageType.isValid(type)) {
            return null;
        }
        String deviceIdentification = oo.getDeviceIdentification();
        String productIdentification = oo.getProductIdentification();
        String currentVersion = StringUtils.defaultString(current.getVersion());

        boolean inTest = false;
        List<DmPackagePo> testBindings = getTestBindings(type, deviceIdentification, productIdentification);
        List<DmPackagePo> testCandidates = new ArrayList<>();
        if (ObjectUtils.isNotEmpty(testBindings)) {
            inTest = true;
            for (DmPackagePo pkg : testBindings) {
                if (OtaVersionUtils.compare(pkg.getVersion(), currentVersion) > 0) {
                    testCandidates.add(pkg);
                }
            }
        }
        List<DmPackagePo> releaseCandidates = new ArrayList<>();
        if (!inTest) {
            for (DmPackagePo pkg : getPublishedPackages(type)) {
                if (!matchProduct(pkg, productIdentification)) {
                    continue;
                }
                if (OtaVersionUtils.compare(pkg.getVersion(), currentVersion) <= 0) {
                    continue;
                }
                if (hitGrayScope(pkg, deviceIdentification, productIdentification)) {
                    releaseCandidates.add(pkg);
                }
            }
        }

        Integer channel = inTest ? DmUpgradeChannel.TEST.getCode() : DmUpgradeChannel.RELEASE.getCode();
        //检测心跳：无论是否命中均留痕（管理端据此确认设备ID，作为测试白名单/设备级灰度录入依据）
        upsertRecord(buildHeartbeat(oo, type, currentVersion, channel));

        //门禁链选包：存在关键版本时取最小关键版本（必须升级），否则取最大版本
        DmPackagePo target = selectTarget(inTest ? testCandidates : releaseCandidates);
        if (target == null) {
            return null;
        }
        //命中留痕（幂等：设备随后上报 CHECK_HIT 阶段会收敛到同一条记录）
        DmUpgradeRecordPo hitInfo = buildRecord(oo, target, inTest, DmPackageUpgradePhase.CHECK_HIT);
        hitInfo.setSuccess(1);
        upsertRecord(hitInfo);
        return buildItem(target, inTest);
    }

    /**
     * 已发布包列表
     */
    private List<DmPackagePo> getPublishedPackages(Integer type) {
        return baseMapper.selectList(new LambdaQueryWrapper<DmPackagePo>()
                .eq(DmPackagePo::getType, type)
                .eq(DmPackagePo::getStatus, DmPackageStatus.PUBLISHED.getCode()));
    }

    /**
     * 产品适用性：包未限定产品（空）或与设备产品一致
     */
    private boolean matchProduct(DmPackagePo pkg, String productIdentification) {
        return StringUtils.isBlank(pkg.getProductIdentification())
                || StringUtils.equals(pkg.getProductIdentification(), productIdentification);
    }

    /**
     * 灰度命中：全量阶梯直接命中；设备级/产品级阶梯按灰度范围匹配
     */
    private boolean hitGrayScope(DmPackagePo pkg, String deviceIdentification, String productIdentification) {
        DmPackageGrayLadder ladder = DmPackageGrayLadder.of(pkg.getGrayLadder());
        if (ladder == null || ladder == DmPackageGrayLadder.FULL) {
            return true;
        }
        List<DmPackageGrayScopePo> scopes = dmPackageGrayScopeMapper.selectList(
                new LambdaQueryWrapper<DmPackageGrayScopePo>()
                        .eq(DmPackageGrayScopePo::getPkgId, pkg.getId())
                        .eq(DmPackageGrayScopePo::getScopeType, ladder.getScopeType().getCode()));
        for (DmPackageGrayScopePo scope : scopes) {
            if (ladder.getScopeType() == DmGrayScopeType.DEVICE
                    && StringUtils.equals(scope.getScopeValue(), deviceIdentification)) {
                return true;
            }
            if (ladder.getScopeType() == DmGrayScopeType.PRODUCT
                    && StringUtils.equals(scope.getScopeValue(), productIdentification)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 测试通道绑定包：设备在测试白名单中的测试中包（不限制版本高低，用于通道判定）
     */
    private List<DmPackagePo> getTestBindings(Integer type, String deviceIdentification,
                                              String productIdentification) {
        List<DmPackageVerifyPo> verifyList = dmPackageVerifyMapper.selectList(
                new LambdaQueryWrapper<DmPackageVerifyPo>()
                        .eq(DmPackageVerifyPo::getDeviceIdentification, deviceIdentification)
                        .eq(DmPackageVerifyPo::getStatus, 1));
        if (ObjectUtils.isEmpty(verifyList)) {
            return Collections.emptyList();
        }
        Set<Long> pkgIds = verifyList.stream().map(DmPackageVerifyPo::getPkgId).collect(Collectors.toSet());
        List<DmPackagePo> pkgs = baseMapper.selectList(new LambdaQueryWrapper<DmPackagePo>()
                .in(DmPackagePo::getId, pkgIds)
                .eq(DmPackagePo::getType, type)
                .eq(DmPackagePo::getStatus, DmPackageStatus.TESTING.getCode()));
        return pkgs.stream().filter(p -> matchProduct(p, productIdentification)).collect(Collectors.toList());
    }

    /**
     * 门禁链选包：有关键版本取最小关键版本；否则取最大版本
     */
    private DmPackagePo selectTarget(List<DmPackagePo> candidates) {
        if (ObjectUtils.isEmpty(candidates)) {
            return null;
        }
        List<DmPackagePo> keyPackages = candidates.stream()
                .filter(p -> Integer.valueOf(1).equals(p.getKeyVersionFlag()))
                .sorted((a, b) -> OtaVersionUtils.compare(a.getVersion(), b.getVersion()))
                .collect(Collectors.toList());
        if (!keyPackages.isEmpty()) {
            return keyPackages.get(0);
        }
        return candidates.stream()
                .max((a, b) -> OtaVersionUtils.compare(a.getVersion(), b.getVersion()))
                .orElse(null);
    }

    /**
     * 构建升级项
     */
    private OtaUpgradeItemVo buildItem(DmPackagePo pkg, boolean fromTest) {
        OtaUpgradeItemVo item = new OtaUpgradeItemVo();
        item.setType(pkg.getType());
        DmPackageType type = DmPackageType.of(pkg.getType());
        item.setTypeName(type == null ? null : type.getMsg());
        item.setPkgId(pkg.getId());
        item.setName(pkg.getName());
        item.setVersion(pkg.getVersion());
        item.setForceUpdate(Integer.valueOf(1).equals(pkg.getUpgradeMode())
                || Integer.valueOf(1).equals(pkg.getKeyVersionFlag()) ? 1 : 0);
        item.setMustPass(Integer.valueOf(1).equals(pkg.getKeyVersionFlag()) ? 1 : 0);
        item.setDownloadUrl(pkg.getUrl());
        item.setFileMd5(pkg.getFileMd5());
        item.setFileSize(pkg.getFileSize());
        item.setFileName(pkg.getFileName());
        item.setChangelog(pkg.getChangelog());
        item.setChannel(fromTest ? DmUpgradeChannel.TEST.getCode() : DmUpgradeChannel.RELEASE.getCode());
        item.setPublishStrategy(pkg.getPublishStrategy());
        item.setGrayLadder(pkg.getGrayLadder());
        return item;
    }

    /**
     * 构建检测心跳记录（不关联具体版本包，仅留痕设备检测行为）
     */
    private DmUpgradeRecordPo buildHeartbeat(DmOtaCheckOo oo, Integer type, String currentVersion, Integer channel) {
        DmUpgradeRecordPo record = new DmUpgradeRecordPo();
        record.setType(type);
        record.setDeviceIdentification(oo.getDeviceIdentification());
        record.setProductIdentification(oo.getProductIdentification());
        record.setFromVersion(currentVersion);
        record.setToVersion(currentVersion);
        record.setChannel(channel);
        record.setPhase(DmPackageUpgradePhase.CHECK.getCode());
        record.setProgress(0);
        record.setSuccess(1);
        record.setUpgradeTime(LocalDateTime.now());
        return record;
    }

    /**
     * 构建命中记录
     */
    private DmUpgradeRecordPo buildRecord(DmOtaCheckOo oo, DmPackagePo pkg, boolean fromTest,
                                          DmPackageUpgradePhase phase) {
        DmUpgradeRecordPo record = new DmUpgradeRecordPo();
        record.setPkgId(pkg.getId());
        record.setType(pkg.getType());
        record.setDeviceIdentification(oo.getDeviceIdentification());
        record.setProductIdentification(oo.getProductIdentification());
        record.setFromVersion(findVersion(oo.getVersions(), pkg.getType()));
        record.setToVersion(pkg.getVersion());
        record.setChannel(fromTest ? DmUpgradeChannel.TEST.getCode() : DmUpgradeChannel.RELEASE.getCode());
        record.setPhase(phase.getCode());
        record.setProgress(phase == DmPackageUpgradePhase.CHECK_HIT ? 5 : 0);
        record.setUpgradeTime(LocalDateTime.now());
        return record;
    }

    private String findVersion(List<DmOtaVersionOo> versions, Integer type) {
        if (versions == null) {
            return null;
        }
        for (DmOtaVersionOo v : versions) {
            if (v.getType() != null && v.getType().equals(type)) {
                return v.getVersion();
            }
        }
        return null;
    }

    /**
     * 幂等 upsert：同一设备同一类型同一目标版本同一阶段仅保留一条
     */
    private void upsertRecord(DmUpgradeRecordPo record) {
        DmUpgradeRecordPo exist = dmUpgradeRecordMapper.selectOne(new LambdaQueryWrapper<DmUpgradeRecordPo>()
                .eq(DmUpgradeRecordPo::getType, record.getType())
                .eq(DmUpgradeRecordPo::getDeviceIdentification, record.getDeviceIdentification())
                .eq(DmUpgradeRecordPo::getToVersion, record.getToVersion())
                .eq(DmUpgradeRecordPo::getPhase, record.getPhase())
                .last("LIMIT 1"));
        if (exist == null) {
            dmUpgradeRecordMapper.insert(record);
        } else {
            record.setId(exist.getId());
            dmUpgradeRecordMapper.updateById(record);
        }
    }

    @Override
    public void report(DmOtaReportOo oo) {
        if (StringUtils.isBlank(oo.getDeviceIdentification())) {
            throw new ServiceException("设备标识不能为空");
        }
        if (!DmPackageType.isValid(oo.getType())) {
            throw new ServiceException("包类型不合法");
        }
        //未知升级阶段静默忽略（设备端可能上报预留/未收录阶段，不影响主流程）
        if (!DmPackageUpgradePhase.isValid(oo.getPhase())) {
            log.debug("[report][忽略未知升级阶段, device: {}, phase: {}]",
                    oo.getDeviceIdentification(), oo.getPhase());
            return;
        }
        //目标版本对应的版本包（取最新一条，可能为空：包已删除等场景仍记录审计）
        DmPackagePo pkg = baseMapper.selectOne(new LambdaQueryWrapper<DmPackagePo>()
                .eq(DmPackagePo::getType, oo.getType())
                .eq(DmPackagePo::getVersion, oo.getToVersion())
                .orderByDesc(DmPackagePo::getId)
                .last("LIMIT 1"));
        DmUpgradeRecordPo record = new DmUpgradeRecordPo();
        record.setPkgId(pkg == null ? null : pkg.getId());
        record.setType(oo.getType());
        record.setDeviceIdentification(oo.getDeviceIdentification());
        record.setDeviceName(oo.getDeviceIdentification());
        record.setProductIdentification(oo.getProductIdentification());
        record.setFromVersion(oo.getFromVersion());
        record.setToVersion(oo.getToVersion());
        record.setChannel(oo.getChannel());
        record.setPhase(oo.getPhase());
        record.setProgress(oo.getProgress());
        record.setSuccess(oo.getSuccess());
        record.setErrorCode(oo.getErrorCode());
        record.setErrorMsg(oo.getErrorMsg());
        record.setCostMs(oo.getCostMs());
        record.setUpgradeTime(LocalDateTime.now());
        //设备名称补全
        Device device = findDevice(oo.getDeviceIdentification());
        if (device != null) {
            record.setDeviceName(device.getDeviceName());
            if (StringUtils.isBlank(record.getProductIdentification())) {
                record.setProductIdentification(device.getProductIdentification());
            }
            //启动成功后同步设备当前版本
            if (DmPackageUpgradePhase.LAUNCH_OK.getCode().equals(oo.getPhase())) {
                updateDeviceVersion(device, oo.getToVersion());
            }
        }
        //幂等 upsert：同一设备同一类型同一目标版本同一阶段仅保留一条
        DmUpgradeRecordPo exist = dmUpgradeRecordMapper.selectOne(new LambdaQueryWrapper<DmUpgradeRecordPo>()
                .eq(DmUpgradeRecordPo::getType, oo.getType())
                .eq(DmUpgradeRecordPo::getDeviceIdentification, oo.getDeviceIdentification())
                .eq(DmUpgradeRecordPo::getToVersion, oo.getToVersion())
                .eq(DmUpgradeRecordPo::getPhase, oo.getPhase())
                .last("LIMIT 1"));
        if (exist == null) {
            dmUpgradeRecordMapper.insert(record);
        } else {
            record.setId(exist.getId());
            dmUpgradeRecordMapper.updateById(record);
        }
    }

    /**
     * 查询设备（仅取一条）
     */
    private Device findDevice(String deviceIdentification) {
        List<Device> devices = deviceMapper
                .selectDeviceByDeviceIdentificationList(Collections.singletonList(deviceIdentification));
        return ObjectUtils.isEmpty(devices) ? null : devices.get(0);
    }

    /**
     * 启动成功后更新设备当前版本
     */
    private void updateDeviceVersion(Device device, String toVersion) {
        try {
            Device update = new Device();
            update.setId(device.getId());
            update.setDeviceVersion(toVersion);
            deviceMapper.updateByPrimaryKeySelective(update);
        } catch (Exception e) {
            log.warn("更新设备版本失败. device:{}, toVersion:{}", device.getDeviceIdentification(), toVersion, e);
        }
    }
}
