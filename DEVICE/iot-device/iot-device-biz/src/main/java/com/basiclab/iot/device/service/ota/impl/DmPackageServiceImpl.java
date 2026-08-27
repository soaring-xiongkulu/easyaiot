package com.basiclab.iot.device.service.ota.impl;

import cn.hutool.core.map.MapUtil;
import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.domain.LoginUser;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.common.utils.JSONUtils;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import com.basiclab.iot.device.constant.MinioConstant;
import com.basiclab.iot.device.dal.dataobject.DmPackageGrayScopePo;
import com.basiclab.iot.device.dal.dataobject.DmPackagePo;
import com.basiclab.iot.device.dal.dataobject.DmPackagePublishPo;
import com.basiclab.iot.device.dal.dataobject.DmPackageVerifyPo;
import com.basiclab.iot.device.dal.pgsql.device.DeviceMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageGrayScopeMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackagePublishMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageVerifyMapper;
import com.basiclab.iot.device.dal.pgsql.ota.DmUpgradeRecordMapper;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.ota.oo.DmBatchAddVerifyOo;
import com.basiclab.iot.device.domain.ota.oo.DmGrayScopeOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageEditOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageExpandGrayOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackagePromoteGrayOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackagePublishOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageTestResultOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageWithdrawOo;
import com.basiclab.iot.device.domain.ota.qo.DmPackagePageQo;
import com.basiclab.iot.device.domain.ota.qo.DmUpgradeRecordPageQo;
import com.basiclab.iot.device.domain.ota.qo.DmVerifyPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmGrayScopeVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackagePageVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackageVersionVo;
import com.basiclab.iot.device.domain.ota.vo.DmUpgradeRecordVo;
import com.basiclab.iot.device.domain.ota.vo.DmUpgradeStatsVo;
import com.basiclab.iot.device.domain.ota.vo.DmVerifyVo;
import com.basiclab.iot.device.domain.ota.vo.DmWhiteGroupVo;
import com.basiclab.iot.device.enums.ota.DmGrayScopeType;
import com.basiclab.iot.device.enums.ota.DmPackageGrayLadder;
import com.basiclab.iot.device.enums.ota.DmPackagePublishStrategy;
import com.basiclab.iot.device.enums.ota.DmPackageStatus;
import com.basiclab.iot.device.enums.ota.DmPackageUpgradePhase;
import com.basiclab.iot.device.service.ota.DmPackageService;
import com.basiclab.iot.file.RemoteFileService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
@Service
@Slf4j
public class DmPackageServiceImpl extends ServiceImpl<DmPackageMapper, DmPackagePo> implements DmPackageService {

    /**
     * 覆盖率达到该阈值时建议灰度升阶
     */
    private static final double PROMOTE_COVERAGE_THRESHOLD = 0.8D;

    @Resource
    private RemoteFileService remoteFileService;

    @Resource
    private DmPackageVerifyMapper dmPackageVerifyMapper;

    @Resource
    private DmPackagePublishMapper dmPackagePublishMapper;

    @Resource
    private DmPackageGrayScopeMapper dmPackageGrayScopeMapper;

    @Resource
    private DmUpgradeRecordMapper dmUpgradeRecordMapper;

    @Resource
    private DeviceMapper deviceMapper;

    @Override
    public List<DmPackagePageVo> list(DmPackagePageQo packagePageQo) {
        return baseMapper.getPackageListByCondition(packagePageQo);
    }

    @Override
    public void createPackage(DmPackageAddOo dmPackageAddOo) throws IOException {
        DmPackagePo dmPackageAddPo = JSONUtils.copy(dmPackageAddOo, DmPackagePo.class);
        //新增版本包
        dmPackageAddPo.setStatus(DmPackageStatus.UNVERIFIED.getCode());
        dmPackageAddPo.setUploadTime(LocalDateTime.now());
        dmPackageAddPo.setFileMd5(dmPackageAddOo.getMd5());
        dmPackageAddPo.setRemark(dmPackageAddOo.getRemark());
        baseMapper.insert(dmPackageAddPo);
    }

    @Override
    public String uploadPackage(MultipartFile file) throws Exception {
        return remoteFileService.upload(file).getData().getUrl();
    }

    @Override
    public void editPackage(DmPackageEditOo dmPackageEditOo) throws IOException {
        //更新版本包
        DmPackagePo dmPackagePo = JSONUtils.copy(dmPackageEditOo, DmPackagePo.class);
        dmPackagePo.setId(dmPackageEditOo.getId());
        if (StringUtils.isEmpty(dmPackageEditOo.getUrl())) {
            dmPackagePo.setUrl(null);
            dmPackagePo.setFileMd5(null);
        } else {
            dmPackagePo.setUrl(dmPackageEditOo.getUrl());
            dmPackagePo.setFileMd5(dmPackageEditOo.getMd5());
        }
        dmPackagePo.setRemark(dmPackageEditOo.getRemark());
        baseMapper.updateById(dmPackagePo);
    }

    @Override
    @Transactional
    public String deletePackage(Long packageId) {
        //获取当前登录用户
        LoginUser loginUser = SecurityFrameworkUtils.getLoginUser();
        //查询版本包信息
        DmPackagePo dmPackagePo = baseMapper.selectById(packageId);
        log.info("删除版本包. adminUserId:{}, dmPackagePo:{}", loginUser.getId(), JSONObject.toJSONString(dmPackagePo));
        //删除版本包
        baseMapper.deleteById(packageId);
        //删除oss保存的版本包
        if (!ObjectUtils.isEmpty(dmPackagePo) && !StringUtils.isEmpty(dmPackagePo.getUrl())) {
            R<Object> objectR = remoteFileService.getDataConfig();
            Map<Object, Object> params = MapUtil.builder()
                    .put(MinioConstant.BUCKETNAME, ((Map) objectR.getData()).get(MinioConstant.BUCKETNAME))
                    .put(MinioConstant.OBJECTNAME, dmPackagePo.getUrl())
                    .build();
            R<String> stringR = remoteFileService.removeFile(params);
            log.info("删除文件结果({})", stringR.getMsg());
        }
        return JSONObject.toJSONString(dmPackagePo);
    }

    @Override
    public List<DmPackageVersionVo> versionList(Integer type) {
        return baseMapper.getVersionListByType(type);
    }

    @Override
    public void submitTest(Long packageId) {
        DmPackagePo pkg = getPackageOrThrow(packageId);
        if (!DmPackageStatus.UNVERIFIED.getCode().equals(pkg.getStatus())) {
            throw new ServiceException("仅未验证状态的版本包可以提交测试");
        }
        DmPackagePo update = new DmPackagePo();
        update.setId(packageId);
        update.setStatus(DmPackageStatus.TESTING.getCode());
        baseMapper.updateById(update);
    }

    @Override
    public void testResult(DmPackageTestResultOo oo) {
        DmPackagePo pkg = getPackageOrThrow(oo.getId());
        if (!DmPackageStatus.TESTING.getCode().equals(pkg.getStatus())) {
            throw new ServiceException("仅测试中状态的版本包可以录入测试结果");
        }
        LoginUser loginUser = SecurityFrameworkUtils.getLoginUser();
        DmPackagePo update = new DmPackagePo();
        update.setId(oo.getId());
        update.setTestPassed(Boolean.TRUE.equals(oo.getPassed()) ? 1 : 0);
        update.setTestRemark(oo.getRemark());
        update.setTestBy(loginUser == null ? null : String.valueOf(loginUser.getId()));
        update.setTestTime(LocalDateTime.now());
        if (!Boolean.TRUE.equals(oo.getPassed())) {
            //测试未通过，回到未验证状态，待修复后重新提交测试
            update.setStatus(DmPackageStatus.UNVERIFIED.getCode());
        }
        baseMapper.updateById(update);
    }

    @Override
    @Transactional
    public void publish(DmPackagePublishOo oo) {
        DmPackagePo pkg = getPackageOrThrow(oo.getId());
        if (DmPackageStatus.PUBLISHED.getCode().equals(pkg.getStatus())) {
            throw new ServiceException("版本包已发布，请先撤回再重新发布");
        }
        //未验证/测试中的包需要测试通过或跳过验证
        if (!Boolean.TRUE.equals(oo.getSkipVerify()) && !Integer.valueOf(1).equals(pkg.getTestPassed())) {
            throw new ServiceException("版本包测试未通过，不允许发布（或勾选跳过验证）");
        }
        DmPackagePublishStrategy strategy = DmPackagePublishStrategy.of(oo.getPublishStrategy());
        if (strategy == null) {
            throw new ServiceException("发布策略不合法");
        }
        DmPackageGrayLadder ladder;
        if (strategy == DmPackagePublishStrategy.FULL) {
            ladder = DmPackageGrayLadder.FULL;
        } else {
            ladder = DmPackageGrayLadder.of(oo.getGrayLadder());
            if (ladder == null || ladder == DmPackageGrayLadder.FULL) {
                throw new ServiceException("灰度发布必须指定设备级或产品级灰度阶梯");
            }
        }
        //同类型下其他已发布的版本包自动撤回，保证同一类型同一时刻只有一个活动版本
        List<DmPackagePo> sameTypePublished = baseMapper.selectList(new LambdaQueryWrapper<DmPackagePo>()
                .eq(DmPackagePo::getType, pkg.getType())
                .eq(DmPackagePo::getStatus, DmPackageStatus.PUBLISHED.getCode()));
        for (DmPackagePo old : sameTypePublished) {
            withdrawInternal(old, "被新版本替换");
        }
        //创建发布记录
        DmPackagePublishPo publish = new DmPackagePublishPo();
        publish.setPkgId(oo.getId());
        publish.setPublishStrategy(strategy.getCode());
        publish.setGrayLadder(ladder.getCode());
        publish.setStatus(1);
        publish.setPublishTime(LocalDateTime.now());
        dmPackagePublishMapper.insert(publish);
        //写入灰度范围
        if (strategy == DmPackagePublishStrategy.GRAY && ObjectUtils.isNotEmpty(oo.getGrayScopes())) {
            replaceGrayScopes(publish.getId(), oo.getId(), ladder, oo.getGrayScopes());
        }
        //更新版本包状态
        DmPackagePo update = new DmPackagePo();
        update.setId(oo.getId());
        update.setStatus(DmPackageStatus.PUBLISHED.getCode());
        update.setPublishStrategy(strategy.getCode());
        update.setGrayLadder(ladder.getCode());
        update.setPublishTime(LocalDateTime.now());
        update.setWithdrawReason(null);
        update.setWithdrawTime(null);
        baseMapper.updateById(update);
    }

    @Override
    @Transactional
    public void expandGray(DmPackageExpandGrayOo oo) {
        DmPackagePo pkg = getPackageOrThrow(oo.getId());
        DmPackagePublishPo publish = getActivePublishOrThrow(oo.getId(), pkg);
        DmPackageGrayLadder ladder = DmPackageGrayLadder.of(publish.getGrayLadder());
        if (ladder == null || ladder.getScopeType() == null) {
            throw new ServiceException("当前灰度阶梯不支持扩大范围");
        }
        if (ObjectUtils.isEmpty(oo.getGrayScopes())) {
            throw new ServiceException("请选择要添加的灰度范围");
        }
        replaceGrayScopes(publish.getId(), oo.getId(), ladder, oo.getGrayScopes(), false);
    }

    @Override
    @Transactional
    public void promoteGray(DmPackagePromoteGrayOo oo) {
        DmPackagePo pkg = getPackageOrThrow(oo.getId());
        DmPackagePublishPo publish = getActivePublishOrThrow(oo.getId(), pkg);
        DmPackageGrayLadder current = DmPackageGrayLadder.of(publish.getGrayLadder());
        DmPackageGrayLadder target = DmPackageGrayLadder.of(oo.getTargetLadder());
        if (current == null || target == null) {
            throw new ServiceException("灰度阶梯不合法");
        }
        if (!current.isAdjacentNext(target)) {
            throw new ServiceException("仅支持相邻升阶：设备级→产品级→全量");
        }
        if (target.getScopeType() != null) {
            //升阶到新的灰度阶梯，替换为对应阶梯的范围
            dmPackageGrayScopeMapper.delete(new LambdaQueryWrapper<DmPackageGrayScopePo>()
                    .eq(DmPackageGrayScopePo::getPublishId, publish.getId())
                    .eq(DmPackageGrayScopePo::getPkgId, oo.getId()));
            if (ObjectUtils.isNotEmpty(oo.getGrayScopes())) {
                replaceGrayScopes(publish.getId(), oo.getId(), target, oo.getGrayScopes());
            }
        } else {
            //升阶到全量，清理灰度范围
            dmPackageGrayScopeMapper.delete(new LambdaQueryWrapper<DmPackageGrayScopePo>()
                    .eq(DmPackageGrayScopePo::getPublishId, publish.getId())
                    .eq(DmPackageGrayScopePo::getPkgId, oo.getId()));
        }
        DmPackagePublishPo publishUpdate = new DmPackagePublishPo();
        publishUpdate.setId(publish.getId());
        publishUpdate.setGrayLadder(target.getCode());
        dmPackagePublishMapper.updateById(publishUpdate);

        DmPackagePo update = new DmPackagePo();
        update.setId(oo.getId());
        update.setGrayLadder(target.getCode());
        baseMapper.updateById(update);
    }

    @Override
    @Transactional
    public void withdraw(DmPackageWithdrawOo oo) {
        DmPackagePo pkg = getPackageOrThrow(oo.getId());
        if (!DmPackageStatus.PUBLISHED.getCode().equals(pkg.getStatus())) {
            throw new ServiceException("仅已发布状态的版本包可以撤回");
        }
        withdrawInternal(pkg, oo.getReason());
    }

    @Override
    public List<DmVerifyVo> getVerifyList(DmVerifyPageQo qo) {
        return dmPackageVerifyMapper.getVerifyPageList(qo);
    }

    @Override
    @Transactional
    public void batchAddVerify(DmBatchAddVerifyOo oo) {
        DmPackagePo pkg = getPackageOrThrow(oo.getPkgId());
        if (ObjectUtils.isEmpty(oo.getDeviceIdentificationList())) {
            throw new ServiceException("请选择要添加的设备");
        }
        //查询设备名称
        Map<String, Device> deviceMap = deviceMapper
                .selectDeviceByDeviceIdentificationList(oo.getDeviceIdentificationList())
                .stream()
                .collect(Collectors.toMap(Device::getDeviceIdentification, Function.identity(), (a, b) -> a));
        List<DmPackageVerifyPo> exists = dmPackageVerifyMapper.selectList(new LambdaQueryWrapper<DmPackageVerifyPo>()
                .eq(DmPackageVerifyPo::getPkgId, oo.getPkgId())
                .eq(DmPackageVerifyPo::getStatus, 1)
                .in(DmPackageVerifyPo::getDeviceIdentification, oo.getDeviceIdentificationList()));
        Set<String> existsDeviceSet = exists.stream()
                .map(DmPackageVerifyPo::getDeviceIdentification)
                .collect(Collectors.toSet());
        List<DmPackageVerifyPo> toInsert = new ArrayList<>();
        for (String deviceIdentification : oo.getDeviceIdentificationList()) {
            if (existsDeviceSet.contains(deviceIdentification)) {
                continue;
            }
            DmPackageVerifyPo verify = new DmPackageVerifyPo();
            verify.setPkgId(oo.getPkgId());
            verify.setDeviceIdentification(deviceIdentification);
            Device device = deviceMap.get(deviceIdentification);
            verify.setDeviceName(device == null ? null : device.getDeviceName());
            verify.setStatus(1);
            verify.setRemark("批量添加");
            toInsert.add(verify);
        }
        if (!toInsert.isEmpty()) {
            toInsert.forEach(dmPackageVerifyMapper::insert);
        }
        log.info("批量添加白名单. pkgId:{}, add:{}, skip:{}", oo.getPkgId(), toInsert.size(),
                oo.getDeviceIdentificationList().size() - toInsert.size());
    }

    @Override
    @Transactional
    public void deleteVerify(List<Long> ids) {
        if (ObjectUtils.isEmpty(ids)) {
            return;
        }
        dmPackageVerifyMapper.deleteBatchIds(ids);
    }

    @Override
    public List<DmWhiteGroupVo> getWhiteGroupList() {
        return dmPackageVerifyMapper.countDeviceGroupByProduct();
    }

    @Override
    public List<DmGrayScopeVo> getGrayScopes(Long pkgId) {
        DmPackagePo pkg = baseMapper.selectById(pkgId);
        if (pkg == null) {
            return Collections.emptyList();
        }
        List<DmPackageGrayScopePo> scopes = dmPackageGrayScopeMapper.selectList(new LambdaQueryWrapper<DmPackageGrayScopePo>()
                .eq(DmPackageGrayScopePo::getPkgId, pkgId)
                .orderByAsc(DmPackageGrayScopePo::getScopeType));
        List<DmGrayScopeVo> result = new ArrayList<>();
        for (DmPackageGrayScopePo scope : scopes) {
            DmGrayScopeVo vo = new DmGrayScopeVo();
            vo.setScopeType(scope.getScopeType());
            DmGrayScopeType scopeType = DmGrayScopeType.of(scope.getScopeType());
            vo.setScopeTypeName(scopeType == null ? null : scopeType.getMsg());
            vo.setScopeValue(scope.getScopeValue());
            result.add(vo);
        }
        return result;
    }

    @Override
    public DmUpgradeStatsVo getUpgradeStats(Long pkgId) {
        DmUpgradeStatsVo stats = new DmUpgradeStatsVo();
        LocalDateTime startTime = LocalDateTime.now().minusDays(7);
        long checkHitCount = dmUpgradeRecordMapper.countDistinctDeviceByPhase(pkgId, DmPackageUpgradePhase.CHECK_HIT.getCode(), startTime);
        long launchOkCount = dmUpgradeRecordMapper.countDistinctDeviceByPhase(pkgId, DmPackageUpgradePhase.LAUNCH_OK.getCode(), startTime);
        long installSuccess = dmUpgradeRecordMapper.countInstallSuccess(pkgId, startTime);
        long installTotal = dmUpgradeRecordMapper.countInstallTotal(pkgId, startTime);
        stats.setCheckHitCount(checkHitCount);
        stats.setLaunchOkCount(launchOkCount);
        stats.setCoverage(checkHitCount == 0 ? 0D : round2((double) launchOkCount / checkHitCount));
        stats.setSuccessRate(installTotal == 0 ? 0D : round2((double) installSuccess / installTotal));
        //漏斗：补齐各阶段，缺省为0
        List<DmUpgradeStatsVo.DmFunnelItemVo> funnel = new ArrayList<>(dmUpgradeRecordMapper.countFunnelByPhase(pkgId, startTime));
        Map<Integer, DmUpgradeStatsVo.DmFunnelItemVo> funnelMap = funnel.stream()
                .collect(Collectors.toMap(DmUpgradeStatsVo.DmFunnelItemVo::getPhase, Function.identity(), (a, b) -> a));
        for (DmPackageUpgradePhase phase : DmPackageUpgradePhase.values()) {
            if (!funnelMap.containsKey(phase.getCode())) {
                DmUpgradeStatsVo.DmFunnelItemVo item = new DmUpgradeStatsVo.DmFunnelItemVo();
                item.setPhase(phase.getCode());
                item.setPhaseName(phase.getMsg());
                item.setDeviceCount(0L);
                funnel.add(item);
            }
        }
        funnel.sort((a, b) -> Integer.compare(a.getPhase(), b.getPhase()));
        stats.setFunnel(funnel);
        stats.setErrorTops(dmUpgradeRecordMapper.countErrorTops(pkgId, startTime));
        //升阶建议：灰度中且覆盖率达标
        DmPackagePo pkg = baseMapper.selectById(pkgId);
        if (pkg != null && DmPackageStatus.PUBLISHED.getCode().equals(pkg.getStatus())
                && DmPackagePublishStrategy.GRAY.getCode().equals(pkg.getPublishStrategy())) {
            DmPackageGrayLadder ladder = DmPackageGrayLadder.of(pkg.getGrayLadder());
            if (ladder != null && ladder != DmPackageGrayLadder.FULL && checkHitCount > 0
                    && (double) launchOkCount / checkHitCount >= PROMOTE_COVERAGE_THRESHOLD) {
                stats.setSuggestPromote(true);
                stats.setNextLadder(ladder.next().getCode());
            } else {
                stats.setSuggestPromote(false);
            }
        }
        return stats;
    }

    @Override
    public List<DmUpgradeRecordVo> getUpgradeRecords(DmUpgradeRecordPageQo qo) {
        return dmUpgradeRecordMapper.getUpgradeRecordPageList(qo);
    }

    /**
     * 撤回指定版本包（含发布记录失效）
     */
    private void withdrawInternal(DmPackagePo pkg, String reason) {
        List<DmPackagePublishPo> publishes = dmPackagePublishMapper.selectList(new LambdaQueryWrapper<DmPackagePublishPo>()
                .eq(DmPackagePublishPo::getPkgId, pkg.getId())
                .eq(DmPackagePublishPo::getStatus, 1));
        for (DmPackagePublishPo publish : publishes) {
            DmPackagePublishPo publishUpdate = new DmPackagePublishPo();
            publishUpdate.setId(publish.getId());
            publishUpdate.setStatus(0);
            publishUpdate.setWithdrawReason(reason);
            publishUpdate.setWithdrawTime(LocalDateTime.now());
            dmPackagePublishMapper.updateById(publishUpdate);
        }
        DmPackagePo update = new DmPackagePo();
        update.setId(pkg.getId());
        update.setStatus(DmPackageStatus.WITHDRAWN.getCode());
        update.setWithdrawReason(reason);
        update.setWithdrawTime(LocalDateTime.now());
        baseMapper.updateById(update);
    }

    /**
     * 替换灰度范围（先删后插）
     */
    private void replaceGrayScopes(Long publishId, Long pkgId, DmPackageGrayLadder ladder, List<DmGrayScopeOo> scopes) {
        replaceGrayScopes(publishId, pkgId, ladder, scopes, true);
    }

    /**
     * 写入灰度范围，append=false 时先删除已有范围
     */
    private void replaceGrayScopes(Long publishId, Long pkgId, DmPackageGrayLadder ladder,
                                   List<DmGrayScopeOo> scopes, boolean append) {
        if (!append) {
            dmPackageGrayScopeMapper.delete(new LambdaQueryWrapper<DmPackageGrayScopePo>()
                    .eq(DmPackageGrayScopePo::getPublishId, publishId)
                    .eq(DmPackageGrayScopePo::getPkgId, pkgId));
        }
        //当前阶梯只允许写入对应类型的范围
        Set<Integer> allowedScopeTypes = new java.util.HashSet<>();
        allowedScopeTypes.add(ladder.getScopeType().getCode());
        List<DmPackageGrayScopePo> toInsert = new ArrayList<>();
        for (DmGrayScopeOo scope : ooList(scopes)) {
            if (scope.getScopeType() == null || !allowedScopeTypes.contains(scope.getScopeType())
                    || StringUtils.isEmpty(scope.getScopeValue())) {
                continue;
            }
            DmPackageGrayScopePo grayScope = new DmPackageGrayScopePo();
            grayScope.setPublishId(publishId);
            grayScope.setPkgId(pkgId);
            grayScope.setScopeType(scope.getScopeType());
            grayScope.setScopeValue(scope.getScopeValue());
            toInsert.add(grayScope);
        }
        if (!toInsert.isEmpty()) {
            toInsert.forEach(dmPackageGrayScopeMapper::insert);
        }
    }

    private List<DmGrayScopeOo> ooList(List<DmGrayScopeOo> scopes) {
        return scopes == null ? Collections.emptyList() : scopes;
    }

    private DmPackagePo getPackageOrThrow(Long packageId) {
        DmPackagePo pkg = baseMapper.selectById(packageId);
        if (pkg == null) {
            throw new ServiceException("版本包不存在");
        }
        return pkg;
    }

    private DmPackagePublishPo getActivePublishOrThrow(Long pkgId, DmPackagePo pkg) {
        if (!DmPackageStatus.PUBLISHED.getCode().equals(pkg.getStatus())) {
            throw new ServiceException("版本包未处于发布状态");
        }
        List<DmPackagePublishPo> publishes = dmPackagePublishMapper.selectList(new LambdaQueryWrapper<DmPackagePublishPo>()
                .eq(DmPackagePublishPo::getPkgId, pkgId)
                .eq(DmPackagePublishPo::getStatus, 1)
                .orderByDesc(DmPackagePublishPo::getPublishTime)
                .last("LIMIT 1"));
        if (ObjectUtils.isEmpty(publishes)) {
            throw new ServiceException("未找到有效的发布记录");
        }
        return publishes.get(0);
    }

    private double round2(double value) {
        return Math.round(value * 100D) / 100D;
    }
}
