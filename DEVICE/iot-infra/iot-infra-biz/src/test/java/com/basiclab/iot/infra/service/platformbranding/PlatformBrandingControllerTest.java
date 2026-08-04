package com.basiclab.iot.infra.service.platformbranding;

import cn.hutool.core.io.resource.ResourceUtil;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.infra.controller.admin.platformbranding.PlatformBrandingController;
import com.basiclab.iot.infra.controller.admin.platformbranding.vo.PlatformBrandingImageRespVO;
import com.basiclab.iot.infra.controller.admin.file.vo.file.FileCreateReqVO;
import com.basiclab.iot.infra.controller.admin.file.vo.file.FilePageReqVO;
import com.basiclab.iot.infra.controller.admin.file.vo.file.FilePresignedUrlRespVO;
import com.basiclab.iot.infra.dal.dataobject.file.FileDO;
import com.basiclab.iot.infra.service.file.FileService;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.bind.annotation.GetMapping;

import javax.annotation.security.PermitAll;
import javax.servlet.http.HttpServletResponse;
import java.lang.reflect.Method;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
/**
 * 品牌图片读取控制器测试。
 */
public class PlatformBrandingControllerTest {

    @Test
    public void testGetImage_writesStoredImageContent() throws Exception {
        FileDO file = new FileDO();
        file.setId(7L);
        file.setConfigId(22L);
        file.setPath("branding/logo.jpg");
        file.setType("image/jpeg");
        byte[] content = ResourceUtil.readBytes("file/erweima.jpg");
        FileService fileService = new FileServiceStub(file, content);
        PlatformBrandingController controller = new PlatformBrandingController();
        ReflectionTestUtils.setField(controller, "fileService", fileService);
        MockHttpServletResponse response = new MockHttpServletResponse();

        controller.getImage(7L, response);

        assertEquals(HttpServletResponse.SC_OK, response.getStatus());
        assertEquals("image/jpeg", response.getContentType());
        assertNull(response.getHeader("Content-Disposition"));
        assertArrayEquals(content, response.getContentAsByteArray());
    }

    @Test
    public void testUploadImage_returnsExtensionlessPreviewUrl() throws Exception {
        FileDO file = new FileDO();
        file.setId(7L);
        file.setConfigId(22L);
        file.setName("logo.jpg");
        file.setPath("branding/logo.jpg");
        file.setType("image/jpeg");
        byte[] content = ResourceUtil.readBytes("file/erweima.jpg");
        FileService fileService = new FileServiceStub(file, content);
        PlatformBrandingController controller = new PlatformBrandingController();
        ReflectionTestUtils.setField(controller, "fileService", fileService);
        MockMultipartFile upload = new MockMultipartFile(
                "file", "logo.jpg", "image/jpeg", content);

        CommonResult<PlatformBrandingImageRespVO> result = controller.uploadImage(upload);

        assertEquals(0, result.getCode());
        assertNotNull(result.getData());
        assertEquals(7L, result.getData().getFileId());
        assertEquals("/admin-api/infra/platform-branding/image/view?fileId=7",
                result.getData().getUrl());
    }

    @Test
    public void testGetImage_isAnonymousExtensionlessGetRoute() throws Exception {
        Method method = PlatformBrandingController.class.getMethod(
                "getImage", Long.class, HttpServletResponse.class);

        assertNotNull(method.getAnnotation(PermitAll.class));
        GetMapping getMapping = method.getAnnotation(GetMapping.class);
        assertNotNull(getMapping);
        assertArrayEquals(new String[]{"/image/view"}, getMapping.value());
    }

    private static class FileServiceStub implements FileService {

        private final FileDO file;
        private final byte[] content;

        private FileServiceStub(FileDO file, byte[] content) {
            this.file = file;
            this.content = content;
        }

        @Override
        public FileDO getFile(Long id) {
            assertEquals(file.getId(), id);
            return file;
        }

        @Override
        public byte[] getFileContent(Long configId, String path) {
            assertEquals(file.getConfigId(), configId);
            assertEquals(file.getPath(), path);
            return content;
        }

        @Override
        public PageResult<FileDO> getFilePage(FilePageReqVO pageReqVO) {
            throw new UnsupportedOperationException();
        }

        @Override
        public String createFile(String name, String path, byte[] content) {
            throw new UnsupportedOperationException();
        }

        @Override
        public FileDO createFileRecord(String name, String path, byte[] content) {
            assertEquals(file.getName(), name);
            assertNull(path);
            assertArrayEquals(this.content, content);
            return file;
        }

        @Override
        public Long createFile(FileCreateReqVO createReqVO) {
            throw new UnsupportedOperationException();
        }

        @Override
        public void deleteFile(Long id) {
            throw new UnsupportedOperationException();
        }

        @Override
        public FilePresignedUrlRespVO getFilePresignedUrl(String path) {
            throw new UnsupportedOperationException();
        }
    }
}
