package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteProductService;
import com.basiclab.iot.device.domain.device.vo.CommandWrapperParamReq;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * RemoteProductFallbackFactory
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Component
public class RemoteProductFallbackFactory implements FallbackFactory<RemoteProductService> {

    private static final Logger log = LoggerFactory.getLogger(RemoteProductFallbackFactory.class);

    @Override
    public RemoteProductService create(Throwable throwable) {
        log.error("产品管理服务调用失败:{}", throwable.getMessage());
        return new RemoteProductService() {
            @Override
            public R selectByProductIdentification(String productIdentification) {
                return R.fail("查询产品失败", throwable.getMessage());
            }

            @Override
            public R selectProductServicesById(Long id) {
                return R.fail("查询产品服务信息失败", throwable.getMessage());
            }

            @Override
            public R selectByIdProperties(Long id) {
                return R.fail("查询产品属性失败", throwable.getMessage());
            }

            @Override
            public R selectAllProduct(String status){
                return R.fail("获取所有产品失败", throwable.getMessage());
            }

            @Override
            public R<?> selectProductByProductIdentificationList(List<String> productIdentificationList){
                return R.fail("获取产品失败", throwable.getMessage());
            }

            @Override
            public R<?> issueCommands(CommandWrapperParamReq commandWrapper) {
                return R.fail("下发指令失败", throwable.getMessage());
            }
        };
    }

}
