package com.basiclab.iot.visualize.service.project;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.visualize.controller.admin.project.vo.VisualizeFuxaOpenRespVO;
import com.basiclab.iot.visualize.controller.admin.project.vo.VisualizeProjectPageReqVO;
import com.basiclab.iot.visualize.controller.admin.project.vo.VisualizeProjectPublishReqVO;
import com.basiclab.iot.visualize.controller.admin.project.vo.VisualizeProjectSaveContentReqVO;
import com.basiclab.iot.visualize.controller.admin.project.vo.VisualizeProjectSaveReqVO;
import com.basiclab.iot.visualize.dal.dataobject.project.VisualizeProjectDO;
import com.basiclab.iot.visualize.dal.pgsql.project.VisualizeProjectMapper;
import com.basiclab.iot.visualize.enums.VisualizeProjectTypeEnum;
import com.basiclab.iot.visualize.framework.fuxa.FuxaDemoGuard;
import com.basiclab.iot.visualize.framework.fuxa.FuxaProperties;
import com.basiclab.iot.visualize.framework.fuxa.FuxaSsoClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.FUXA_SSO_FAILED;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.PROJECT_NOT_FOUND;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.PROJECT_NOT_SCADA;
import static com.basiclab.iot.visualize.enums.ErrorCodeConstants.PROJECT_TYPE_INVALID;

@Slf4j
@Service
@Validated
public class VisualizeProjectServiceImpl implements VisualizeProjectService {

    @Resource
    private VisualizeProjectMapper projectMapper;
    @Resource
    private FuxaSsoClient fuxaSsoClient;
    @Resource
    private FuxaProperties fuxaProperties;

    @Override
    public Long createProject(VisualizeProjectSaveReqVO createReqVO) {
        VisualizeProjectDO project = BeanUtils.toBean(createReqVO, VisualizeProjectDO.class);
        if (project.getState() == null) {
            project.setState(-1);
        }
        String projectType = normalizeAndValidateType(createReqVO.getProjectType());
        project.setProjectType(projectType);
        // 组态工程由 FUXA 持久化；平台侧默认挂到编辑器入口，便于一键打开
        if (VisualizeProjectTypeEnum.isScada(projectType)
                && (project.getEditorRef() == null || project.getEditorRef().trim().isEmpty())) {
            project.setEditorRef("/editor");
        }
        projectMapper.insert(project);
        return project.getId();
    }

    @Override
    public void updateProject(VisualizeProjectSaveReqVO updateReqVO) {
        VisualizeProjectDO existing = validateExists(updateReqVO.getId());
        VisualizeProjectDO updateObj = BeanUtils.toBean(updateReqVO, VisualizeProjectDO.class);
        // 类型创建后不可变更，避免大屏/组态数据串线
        updateObj.setProjectType(existing.getProjectType());
        projectMapper.updateById(updateObj);
    }

    @Override
    public void saveContent(VisualizeProjectSaveContentReqVO reqVO) {
        VisualizeProjectDO existing = validateExists(reqVO.getId());
        if (VisualizeProjectTypeEnum.isScada(existing.getProjectType())
                || VisualizeProjectTypeEnum.isTwin(existing.getProjectType())) {
            // 组态与数字孪生内容由各自运行时持久化，后台仅登记元数据
            return;
        }
        VisualizeProjectDO updateObj = new VisualizeProjectDO();
        updateObj.setId(reqVO.getId());
        updateObj.setContent(reqVO.getContent());
        projectMapper.updateById(updateObj);
    }

    @Override
    public void publishProject(VisualizeProjectPublishReqVO reqVO) {
        validateExists(reqVO.getId());
        VisualizeProjectDO updateObj = new VisualizeProjectDO();
        updateObj.setId(reqVO.getId());
        updateObj.setState(reqVO.getState());
        projectMapper.updateById(updateObj);
    }

    @Override
    public void deleteProject(Long id) {
        validateExists(id);
        projectMapper.deleteById(id);
    }

    @Override
    public VisualizeProjectDO getProject(Long id) {
        return projectMapper.selectById(id);
    }

    @Override
    public PageResult<VisualizeProjectDO> getProjectPage(VisualizeProjectPageReqVO pageReqVO) {
        return projectMapper.selectPage(pageReqVO);
    }

    @Override
    public VisualizeFuxaOpenRespVO buildFuxaOpenUrl(Long id, String mode, String editorRef) {
        String resolvedMode = "preview".equalsIgnoreCase(mode) ? "preview" : "edit";
        String ref = editorRef;
        String projectName = null;
        boolean readOnly = false;

        if (id != null) {
            VisualizeProjectDO project = validateExists(id);
            if (!VisualizeProjectTypeEnum.isScada(project.getProjectType())) {
                throw exception(PROJECT_NOT_SCADA);
            }
            projectName = project.getProjectName();
            if (!StringUtils.hasText(ref)) {
                ref = project.getEditorRef();
            }
        }

        // 生产演示保护：强制 preview，避免 SSO 以 admin 进入 /editor 改删工艺图
        if ("edit".equals(resolvedMode)) {
            boolean protectDemo = fuxaProperties.isDemoReadOnly()
                    && FuxaDemoGuard.isProtectedDemo(id, projectName, ref);
            if (fuxaProperties.isForcePreview() || protectDemo) {
                log.info("FUXA open forced to preview (forcePreview={}, demoReadOnly hit={}), id={}, ref={}",
                        fuxaProperties.isForcePreview(), protectDemo, id, ref);
                resolvedMode = "preview";
                readOnly = true;
            }
        }

        // 编辑模式：空引用或仅 /editor 时回退为项目名（与 FUXA Views 画面名对齐）
        if ("edit".equals(resolvedMode)) {
            String trimmed = ref == null ? "" : ref.trim();
            if (!StringUtils.hasText(trimmed) || "/editor".equals(trimmed)) {
                ref = StringUtils.hasText(projectName) ? projectName : trimmed;
            }
        }
        // 预览且引用仍是 /editor：降为运行态首页，避免只读策略下仍跳进编辑器
        if ("preview".equals(resolvedMode)) {
            String trimmed = ref == null ? "" : ref.trim();
            if ("/editor".equals(trimmed) || trimmed.startsWith("/editor?")) {
                ref = StringUtils.hasText(projectName) ? projectName : "";
            }
        }

        VisualizeFuxaOpenRespVO resp = new VisualizeFuxaOpenRespVO();
        resp.setMode(resolvedMode);
        resp.setReadOnly(readOnly);

        if (fuxaSsoClient.isEnabled()) {
            try {
                resp.setUrl(fuxaSsoClient.buildOpenUrl(resolvedMode, ref));
                resp.setSso(true);
                return resp;
            } catch (Exception ex) {
                throw exception(FUXA_SSO_FAILED);
            }
        }

        resp.setUrl(buildDirectFuxaUrl(resolvedMode, ref));
        resp.setSso(false);
        return resp;
    }

    private String buildDirectFuxaUrl(String mode, String editorRef) {
        String base = fuxaProperties.getPublicUrl();
        if (!StringUtils.hasText(base)) {
            base = fuxaProperties.getBaseUrl();
        }
        if (base.endsWith("/")) {
            base = base.substring(0, base.length() - 1);
        }
        String ref = editorRef == null ? "" : editorRef.trim();
        if (ref.startsWith("/")) {
            return base + ref;
        }
        if ("preview".equals(mode)) {
            return StringUtils.hasText(ref)
                    ? base + "/home?view=" + URLEncoder.encode(ref, StandardCharsets.UTF_8)
                    : base + "/home";
        }
        // 编辑模式：带画面名时走同源桥接页写入 FUXA currentview，再进 /editor
        if (StringUtils.hasText(ref)) {
            return base + "/easyaiot-sso.html?mode=edit"
                    + "&view=" + URLEncoder.encode(ref, StandardCharsets.UTF_8)
                    + "&allowOpenWithoutToken=1";
        }
        return base + "/editor";
    }

    private VisualizeProjectDO validateExists(Long id) {
        if (id == null) {
            throw exception(PROJECT_NOT_FOUND);
        }
        VisualizeProjectDO project = projectMapper.selectById(id);
        if (project == null) {
            throw exception(PROJECT_NOT_FOUND);
        }
        return project;
    }

    private String normalizeAndValidateType(String projectType) {
        String normalized = VisualizeProjectTypeEnum.normalize(projectType);
        if (projectType != null && !projectType.isEmpty() && !VisualizeProjectTypeEnum.isValid(projectType)) {
            throw exception(PROJECT_TYPE_INVALID);
        }
        return normalized;
    }

}
