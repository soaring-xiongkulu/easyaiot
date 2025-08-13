//package com.basiclab.iot.device.common.listener;
//
//import com.basiclab.iot.common.constant.CacheConstants;
//import com.basiclab.iot.common.constant.Constants;
//import com.basiclab.iot.common.text.UUID;
//import com.basiclab.iot.common.redis.service.RedisService;
//import com.basiclab.iot.device.domain.device.vo.Device;
//import com.basiclab.iot.device.service.device.DeviceService;
//import lombok.SneakyThrows;
//import lombok.extern.slf4j.Slf4j;
//import org.springframework.beans.factory.annotation.Autowired;
//import org.springframework.data.redis.connection.Message;
//import org.springframework.data.redis.listener.KeyExpirationEventMessageListener;
//import org.springframework.data.redis.listener.RedisMessageListenerContainer;
//import org.springframework.stereotype.Component;
//
//import java.util.concurrent.TimeUnit;
//
///**
// * @Description: Redis Key失效事件监听
// * @author: EasyAIoT
// * @CreateDate: 2022/3/1$ 15:28$
// * @UpdateUser: EasyAIoT
// * @UpdateDate: 2022/3/1$ 15:28$
// * @UpdateRemark: 修改内容
// * @Version: V1.0
// */
//@Component
//@Slf4j
//public class RedisKeyExpirationListener extends KeyExpirationEventMessageListener {
//
//    @Autowired
//    private RedisService redisService;
//    @Autowired
//    private DeviceService deviceService;
//
//    public RedisKeyExpirationListener(RedisMessageListenerContainer listenerContainer) {
//        super(listenerContainer);
//    }
//
//    @SneakyThrows
//    @Override
//    public void onMessage(Message message, byte[] pattern) {
//        String expiredKey = message.toString();
//        // 避免多个服务监听情况下重复消费
//        boolean resultLock = false;
//        String uuid = UUID.getUUID();
//        try {
//            resultLock = redisService.checkLock(expiredKey, uuid, 1000L);
//            if (resultLock) {
//                log.info("获取分布式锁成功-key：{}，value：{}", expiredKey, uuid);
//                if (expiredKey.contains(CacheConstants.DEF_DEVICE)){
//                    log.info("设备信息缓存失效{}",expiredKey);
//                    deviceService.cacheInvalidation(expiredKey.replace(CacheConstants.DEF_DEVICE, ""));
//                }
//            }else {
//                log.info("获取分布式锁失败-key：{}，value：{}", expiredKey, uuid);
//            }
//        }catch (Exception e){
//            log.error(e.getMessage());
//        }finally {
//            if (resultLock) {
//                //释放锁
//                boolean result = redisService.releaseDistributedLock(expiredKey, uuid);
//                if (result) {
//                    log.info("释放分布式锁成功-key：{}，value：{}", expiredKey, uuid);
//                } else {
//                    log.info("释放分布式锁失败-key：{}，value：{}", expiredKey, uuid);
//                }
//            }
//        }
//    }
//}
