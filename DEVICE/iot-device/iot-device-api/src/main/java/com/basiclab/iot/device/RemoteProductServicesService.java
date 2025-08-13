package com.basiclab.iot.device;


import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.factory.RemoteProductServicesFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;


@FeignClient(contextId = "remoteProductServicesService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteProductServicesFallbackFactory.class)
public interface RemoteProductServicesService {



    @GetMapping("/productServices/selectAllByProductIdentificationAndStatus")
    R<?> selectAllByProductIdentificationAndStatus(@RequestParam("productIdentification") String productIdentification,@RequestParam("status") String status);

    @PostMapping ("/productServices/selectProductServicesByIdList")
    R<?> selectProductServicesByIdList(@RequestBody List<Long> serviceIdList);
}
