package com.basiclab.iot.device;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.domain.device.vo.CommandWrapperParamReq;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.device.domain.device.vo.ProductServices;
import com.basiclab.iot.device.factory.RemoteProductFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import javax.validation.Valid;
import java.util.List;

/**
 * @program: EasyAIoT
 * @description: 产品管理服务
 * @packagename: com.basiclab.iot.device.api
 * @author: shisen
 * @date: 2025-07-26
 **/
@FeignClient(contextId = "remoteProductService", value = ServiceNameConstants.IOT_DEVICE, fallbackFactory = RemoteProductFallbackFactory.class)
public interface RemoteProductService {

    /**
     * 通过标识查询产品
     *
     * @param productIdentification
     * @return
     */
    @GetMapping("/product/selectByProductIdentification/{productIdentification}")
    public R<Product> selectByProductIdentification(@PathVariable("productIdentification") String productIdentification);

    /**
     * 查询服务信息
     *
     * @param id
     * @return
     */
    @GetMapping(value = "/productServices/selectProductServicesById/{id}")
    public R<ProductServices> selectProductServicesById(@PathVariable("id") Long id);


    /**
     * 查询属性信息
     *
     * @return
     */
    @GetMapping("/productProperties/selectByIdProperties/{id}")
    public R<ProductProperties> selectByIdProperties(@PathVariable("id") Long id);

    @GetMapping("/product/selectAllProduct/{status}")
    public R<List<Product>> selectAllProduct(@PathVariable("status") String status);

    @PostMapping("/product/selectProductByProductIdentificationList")
    public R<?> selectProductByProductIdentificationList(@RequestBody List<String> productIdentificationList);

    @PostMapping("/product/issueCommands")
    public R<?> issueCommands(@RequestBody @Valid CommandWrapperParamReq commandWrapper);


}
