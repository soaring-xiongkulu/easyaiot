package com.basiclab.iot.visualize.service.deploy;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.visualize.controller.admin.deploy.vo.VisualizeDeployPageReqVO;
import com.basiclab.iot.visualize.controller.admin.deploy.vo.VisualizeDeploySaveReqVO;
import com.basiclab.iot.visualize.dal.dataobject.deploy.VisualizeDeployDO;
import com.basiclab.iot.visualize.dal.dataobject.project.VisualizeProjectDO;
import com.basiclab.iot.visualize.dal.pgsql.deploy.VisualizeDeployMapper;
import com.basiclab.iot.visualize.dal.pgsql.project.VisualizeProjectMapper;
import com.basiclab.iot.visualize.enums.VisualizeProjectTypeEnum;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.util.UUID;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.DEPLOY_CODE_DUPLICATE;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.DEPLOY_NOT_FOUND;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.PROJECT_NOT_FOUND;

@Service
@Validated
public class VisualizeDeployServiceImpl implements VisualizeDeployService {

    @Resource
    private VisualizeDeployMapper deployMapper;
    @Resource
    private VisualizeProjectMapper projectMapper;

    @Override
    public Long createDeploy(VisualizeDeploySaveReqVO createReqVO) {
        VisualizeProjectDO project = validateProject(createReqVO.getProjectId());
        String deployCode = resolveDeployCode(createReqVO.getDeployCode(), null);
        VisualizeDeployDO deploy = BeanUtils.toBean(createReqVO, VisualizeDeployDO.class);
        deploy.setDeployCode(deployCode);
        deploy.setProjectName(project.getProjectName());
        deploy.setStatus(0);
        deploy.setAccessPath(buildAccessPath(project, deployCode));
        deployMapper.insert(deploy);
        return deploy.getId();
    }

    @Override
    public void updateDeploy(VisualizeDeploySaveReqVO updateReqVO) {
        VisualizeDeployDO existing = validateExists(updateReqVO.getId());
        VisualizeProjectDO project = validateProject(updateReqVO.getProjectId());
        String deployCode = resolveDeployCode(updateReqVO.getDeployCode(), existing.getId());
        VisualizeDeployDO updateObj = BeanUtils.toBean(updateReqVO, VisualizeDeployDO.class);
        updateObj.setDeployCode(deployCode);
        updateObj.setProjectName(project.getProjectName());
        updateObj.setAccessPath(buildAccessPath(project, deployCode));
        // 不允许通过 update 直接改状态
        updateObj.setStatus(null);
        deployMapper.updateById(updateObj);
    }

    @Override
    public void deleteDeploy(Long id) {
        validateExists(id);
        deployMapper.deleteById(id);
    }

    @Override
    public VisualizeDeployDO getDeploy(Long id) {
        return deployMapper.selectById(id);
    }

    @Override
    public PageResult<VisualizeDeployDO> getDeployPage(VisualizeDeployPageReqVO pageReqVO) {
        return deployMapper.selectPage(pageReqVO);
    }

    @Override
    public void onlineDeploy(Long id) {
        validateExists(id);
        VisualizeDeployDO updateObj = new VisualizeDeployDO();
        updateObj.setId(id);
        updateObj.setStatus(1);
        deployMapper.updateById(updateObj);
    }

    @Override
    public void offlineDeploy(Long id) {
        validateExists(id);
        VisualizeDeployDO updateObj = new VisualizeDeployDO();
        updateObj.setId(id);
        updateObj.setStatus(2);
        deployMapper.updateById(updateObj);
    }

    private VisualizeDeployDO validateExists(Long id) {
        if (id == null) {
            throw exception(DEPLOY_NOT_FOUND);
        }
        VisualizeDeployDO deploy = deployMapper.selectById(id);
        if (deploy == null) {
            throw exception(DEPLOY_NOT_FOUND);
        }
        return deploy;
    }

    private VisualizeProjectDO validateProject(Long projectId) {
        VisualizeProjectDO project = projectMapper.selectById(projectId);
        if (project == null) {
            throw exception(PROJECT_NOT_FOUND);
        }
        return project;
    }

    private String resolveDeployCode(String requestCode, Long excludeId) {
        String code = (requestCode == null || requestCode.trim().isEmpty())
                ? UUID.randomUUID().toString().replace("-", "").substring(0, 16)
                : requestCode.trim();
        VisualizeDeployDO existed = deployMapper.selectByDeployCode(code);
        if (existed != null && (excludeId == null || !existed.getId().equals(excludeId))) {
            throw exception(DEPLOY_CODE_DUPLICATE);
        }
        return code;
    }

    /**
     * 大屏：VISUALIZE 预览 hash 路径；组态：FUXA 运行态路径（相对 FUXA 基址）
     */
    private String buildAccessPath(VisualizeProjectDO project, String deployCode) {
        if (VisualizeProjectTypeEnum.isTwin(project.getProjectType())) {
            String ref = StringUtils.hasText(project.getEditorRef()) ? project.getEditorRef().trim() : "industrial";
            return "/?project=" + ref + "&deployCode=" + deployCode;
        }
        if (VisualizeProjectTypeEnum.isScada(project.getProjectType())) {
            String ref = project.getEditorRef();
            if (StringUtils.hasText(ref)) {
                String trimmed = ref.trim();
                if (trimmed.startsWith("/")) {
                    return trimmed;
                }
                // 画面名：走 FUXA 运行态并附带 view 提示参数（FUXA 内部仍可手动切画面）
                return "/home?view=" + trimmed;
            }
            return "/home";
        }
        return "/#/chart/preview/" + project.getId() + "?deployCode=" + deployCode;
    }

}
