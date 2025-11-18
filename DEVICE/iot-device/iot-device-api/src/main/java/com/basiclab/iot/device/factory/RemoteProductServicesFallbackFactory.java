package com.basiclab.iot.device.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteProductServicesService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import java.util.List;


/**
 * RemoteProductServicesFallbackFactory
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Component
public class RemoteProductServicesFallbackFactory implements FallbackFactory<RemoteProductServicesService> {

    private static final Logger log = LoggerFactory.getLogger(RemoteProductServicesFallbackFactory.class);

    @Override
    public RemoteProductServicesService create(Throwable throwable) {
        log.error("产品服务管理服务调用失败:{}", throwable.getMessage());
        return new RemoteProductServicesService() {
            @Override
            public R<?> selectAllByProductIdentificationAndStatus( String productIdentification, String status) {
                return R.fail("查询产品服务失败", throwable.getMessage());
            }

            @Override
            public R<?> selectProductServicesByIdList(List<Long> serviceIdList){
                return R.fail("根据服务id列表查询服务失败", throwable.getMessage());
            }

        };
    }

}
