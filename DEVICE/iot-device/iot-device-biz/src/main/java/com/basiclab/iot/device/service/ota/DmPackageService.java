package com.basiclab.iot.device.service.ota;


import com.basiclab.iot.device.domain.ota.oo.DmBatchAddVerifyOo;
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
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
public interface DmPackageService {

    List<DmPackagePageVo> list(DmPackagePageQo packagePageQo);

    void createPackage(DmPackageAddOo dmPackageAddOo) throws IOException;

    String uploadPackage(MultipartFile file) throws Exception;

    void editPackage(DmPackageEditOo dmPackageEditOo) throws IOException;

    String deletePackage(Long packageId);

    List<DmPackageVersionVo> versionList(Integer type);

    /**
     * 提交测试（未验证 → 测试中）
     *
     * @param packageId 版本包ID
     */
    void submitTest(Long packageId);

    /**
     * 测试结果录入（通过后保持测试中等待发布，未通过回到未验证）
     *
     * @param oo 测试结果
     */
    void testResult(DmPackageTestResultOo oo);

    /**
     * 发布（全量/灰度，可跳过测试验证）
     *
     * @param oo 发布参数
     */
    void publish(DmPackagePublishOo oo);

    /**
     * 扩大当前灰度范围（不升阶）
     *
     * @param oo 灰度范围
     */
    void expandGray(DmPackageExpandGrayOo oo);

    /**
     * 灰度升阶（仅允许相邻升阶：设备级→产品级→全量）
     *
     * @param oo 升阶参数
     */
    void promoteGray(DmPackagePromoteGrayOo oo);

    /**
     * 撤回发布
     *
     * @param oo 撤回参数
     */
    void withdraw(DmPackageWithdrawOo oo);

    /**
     * 白名单分页列表
     *
     * @param qo 查询条件
     * @return 白名单记录
     */
    List<DmVerifyVo> getVerifyList(DmVerifyPageQo qo);

    /**
     * 批量添加测试白名单
     *
     * @param oo 参数
     */
    void batchAddVerify(DmBatchAddVerifyOo oo);

    /**
     * 删除白名单记录
     *
     * @param ids 白名单记录ID集合
     */
    void deleteVerify(List<Long> ids);

    /**
     * 白名单分组统计（按产品）
     *
     * @return 分组列表
     */
    List<DmWhiteGroupVo> getWhiteGroupList();

    /**
     * 当前活动发布的灰度范围
     *
     * @param pkgId 版本包ID
     * @return 灰度范围列表
     */
    List<DmGrayScopeVo> getGrayScopes(Long pkgId);

    /**
     * 升级统计（漏斗 + 健康度 + 升阶建议）
     *
     * @param pkgId 版本包ID
     * @return 统计结果
     */
    DmUpgradeStatsVo getUpgradeStats(Long pkgId);

    /**
     * 升级记录分页列表
     *
     * @param qo 查询条件
     * @return 升级记录
     */
    List<DmUpgradeRecordVo> getUpgradeRecords(DmUpgradeRecordPageQo qo);
}
