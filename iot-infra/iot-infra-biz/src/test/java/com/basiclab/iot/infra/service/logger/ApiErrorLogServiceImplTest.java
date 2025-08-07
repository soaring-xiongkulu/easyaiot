package com.basiclab.iot.infra.service.logger;

import com.basiclab.iot.common.enums.UserTypeEnum;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.test.core.ut.BaseDbUnitTest;
import com.basiclab.iot.infra.api.logger.dto.ApiErrorLogCreateReqDTO;
import com.basiclab.iot.infra.controller.admin.logger.vo.apierrorlog.ApiErrorLogPageReqVO;
import com.basiclab.iot.infra.dal.dataobject.logger.ApiErrorLogDO;
import com.basiclab.iot.infra.dal.mysql.logger.ApiErrorLogMapper;
import com.basiclab.iot.infra.enums.ErrorCodeConstants;
import com.basiclab.iot.infra.enums.logger.ApiErrorLogProcessStatusEnum;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Import;

import javax.annotation.Resource;
import java.time.Duration;
import java.util.List;

import static cn.hutool.core.util.RandomUtil.randomEle;
import static com.basiclab.iot.common.utils.date.LocalDateTimeUtils.*;
import static com.basiclab.iot.common.utils.object.ObjectUtils.cloneIgnoreId;
import static com.basiclab.iot.common.test.core.util.AssertUtils.assertPojoEquals;
import static com.basiclab.iot.common.test.core.util.AssertUtils.assertServiceException;
import static com.basiclab.iot.common.test.core.util.RandomUtils.randomLongId;
import static com.basiclab.iot.common.test.core.util.RandomUtils.randomPojo;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@Import(ApiErrorLogServiceImpl.class)
public class ApiErrorLogServiceImplTest extends BaseDbUnitTest {

    @Resource
    private ApiErrorLogServiceImpl apiErrorLogService;

    @Resource
    private ApiErrorLogMapper apiErrorLogMapper;

    @Test
    public void testGetApiErrorLogPage() {
        // mock 数据
        ApiErrorLogDO apiErrorLogDO = randomPojo(ApiErrorLogDO.class, o -> {
            o.setUserId(2233L);
            o.setUserType(UserTypeEnum.ADMIN.getValue());
            o.setApplicationName("iot-test");
            o.setRequestUrl("foo");
            o.setExceptionTime(buildTime(2021, 3, 13));
            o.setProcessStatus(ApiErrorLogProcessStatusEnum.INIT.getStatus());
        });
        apiErrorLogMapper.insert(apiErrorLogDO);
        // 测试 userId 不匹配
        apiErrorLogMapper.insert(cloneIgnoreId(apiErrorLogDO, o -> o.setUserId(3344L)));
        // 测试 userType 不匹配
        apiErrorLogMapper.insert(cloneIgnoreId(apiErrorLogDO, o -> o.setUserType(UserTypeEnum.MEMBER.getValue())));
        // 测试 applicationName 不匹配
        apiErrorLogMapper.insert(cloneIgnoreId(apiErrorLogDO, o -> o.setApplicationName("test")));
        // 测试 requestUrl 不匹配
        apiErrorLogMapper.insert(cloneIgnoreId(apiErrorLogDO, o -> o.setRequestUrl("bar")));
        // 测试 exceptionTime 不匹配：构造一个早期时间 2021-02-06 00:00:00
        apiErrorLogMapper.insert(cloneIgnoreId(apiErrorLogDO, o -> o.setExceptionTime(buildTime(2021, 2, 6))));
        // 测试 progressStatus 不匹配
        apiErrorLogMapper.insert(cloneIgnoreId(apiErrorLogDO, logDO -> logDO.setProcessStatus(ApiErrorLogProcessStatusEnum.DONE.getStatus())));
        // 准备参数
        ApiErrorLogPageReqVO reqVO = new ApiErrorLogPageReqVO();
        reqVO.setUserId(2233L);
        reqVO.setUserType(UserTypeEnum.ADMIN.getValue());
        reqVO.setApplicationName("iot-test");
        reqVO.setRequestUrl("foo");
        reqVO.setExceptionTime(buildBetweenTime(2021, 3, 1, 2021, 3, 31));
        reqVO.setProcessStatus(ApiErrorLogProcessStatusEnum.INIT.getStatus());

        // 调用
        PageResult<ApiErrorLogDO> pageResult = apiErrorLogService.getApiErrorLogPage(reqVO);
        // 断言，只查到了一条符合条件的
        assertEquals(1, pageResult.getTotal());
        assertEquals(1, pageResult.getList().size());
        assertPojoEquals(apiErrorLogDO, pageResult.getList().get(0));
    }

    @Test
    public void testCreateApiErrorLog() {
        // 准备参数
        ApiErrorLogCreateReqDTO createDTO = randomPojo(ApiErrorLogCreateReqDTO.class);

        // 调用
        apiErrorLogService.createApiErrorLog(createDTO);
        // 断言
        ApiErrorLogDO apiErrorLogDO = apiErrorLogMapper.selectOne(null);
        assertPojoEquals(createDTO, apiErrorLogDO);
        assertEquals(ApiErrorLogProcessStatusEnum.INIT.getStatus(), apiErrorLogDO.getProcessStatus());
    }

    @Test
    public void testUpdateApiErrorLogProcess_success() {
        // 准备参数
        ApiErrorLogDO apiErrorLogDO = randomPojo(ApiErrorLogDO.class,
                o -> o.setProcessStatus(ApiErrorLogProcessStatusEnum.INIT.getStatus()));
        apiErrorLogMapper.insert(apiErrorLogDO);
        // 准备参数
        Long id = apiErrorLogDO.getId();
        Integer processStatus = randomEle(ApiErrorLogProcessStatusEnum.values()).getStatus();
        Long processUserId = randomLongId();

        // 调用
        apiErrorLogService.updateApiErrorLogProcess(id, processStatus, processUserId);
        // 断言
        ApiErrorLogDO dbApiErrorLogDO = apiErrorLogMapper.selectById(apiErrorLogDO.getId());
        assertEquals(processStatus, dbApiErrorLogDO.getProcessStatus());
        assertEquals(processUserId, dbApiErrorLogDO.getProcessUserId());
        assertNotNull(dbApiErrorLogDO.getProcessTime());
    }

    @Test
    public void testUpdateApiErrorLogProcess_processed() {
        // 准备参数
        ApiErrorLogDO apiErrorLogDO = randomPojo(ApiErrorLogDO.class,
                o -> o.setProcessStatus(ApiErrorLogProcessStatusEnum.DONE.getStatus()));
        apiErrorLogMapper.insert(apiErrorLogDO);
        // 准备参数
        Long id = apiErrorLogDO.getId();
        Integer processStatus = randomEle(ApiErrorLogProcessStatusEnum.values()).getStatus();
        Long processUserId = randomLongId();

        // 调用，并断言异常
        assertServiceException(() ->
                        apiErrorLogService.updateApiErrorLogProcess(id, processStatus, processUserId),
                ErrorCodeConstants.API_ERROR_LOG_PROCESSED);
    }

    @Test
    public void testUpdateApiErrorLogProcess_notFound() {
        // 准备参数
        Long id = randomLongId();
        Integer processStatus = randomEle(ApiErrorLogProcessStatusEnum.values()).getStatus();
        Long processUserId = randomLongId();

        // 调用，并断言异常
        assertServiceException(() ->
                        apiErrorLogService.updateApiErrorLogProcess(id, processStatus, processUserId),
                ErrorCodeConstants.API_ERROR_LOG_NOT_FOUND);
    }

    @Test
    public void testCleanJobLog() {
        // mock 数据
        ApiErrorLogDO log01 = randomPojo(ApiErrorLogDO.class, o -> o.setCreateTime(addTime(Duration.ofDays(-3))));
        apiErrorLogMapper.insert(log01);
        ApiErrorLogDO log02 = randomPojo(ApiErrorLogDO.class, o -> o.setCreateTime(addTime(Duration.ofDays(-1))));
        apiErrorLogMapper.insert(log02);
        // 准备参数
        Integer exceedDay = 2;
        Integer deleteLimit = 1;

        // 调用
        Integer count = apiErrorLogService.cleanErrorLog(exceedDay, deleteLimit);
        // 断言
        assertEquals(1, count);
        List<ApiErrorLogDO> logs = apiErrorLogMapper.selectList();
        assertEquals(1, logs.size());
        assertEquals(log02, logs.get(0));
    }

}
