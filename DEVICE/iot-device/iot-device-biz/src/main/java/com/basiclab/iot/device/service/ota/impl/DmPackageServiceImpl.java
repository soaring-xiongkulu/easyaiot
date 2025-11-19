package com.basiclab.iot.device.service.ota.impl;

import cn.hutool.core.map.MapUtil;
import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.basiclab.iot.common.domain.LoginUser;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.utils.JSONUtils;
import com.basiclab.iot.common.utils.SecurityFrameworkUtils;
import com.basiclab.iot.device.constant.MinioConstant;
import com.basiclab.iot.device.dal.dataobject.DmPackagePo;
import com.basiclab.iot.device.dal.pgsql.ota.DmPackageMapper;
import com.basiclab.iot.device.domain.ota.oo.DmPackageAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageEditOo;
import com.basiclab.iot.device.domain.ota.qo.DmPackagePageQo;
import com.basiclab.iot.device.domain.ota.vo.DmPackagePageVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackageVersionVo;
import com.basiclab.iot.device.enums.ota.DmPackageStatus;
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
import java.util.List;
import java.util.Map;

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

    @Resource
    private RemoteFileService remoteFileService;

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
}
