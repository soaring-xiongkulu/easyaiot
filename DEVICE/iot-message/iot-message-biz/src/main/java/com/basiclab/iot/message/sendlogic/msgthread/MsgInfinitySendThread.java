package com.basiclab.iot.message.sendlogic.msgthread;

import cn.hutool.json.JSONUtil;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.sendlogic.PushData;
import com.basiclab.iot.message.sendlogic.msgsender.IMsgSender;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.exception.ExceptionUtils;

/**
 * 消息异步发送服务线程
 */
@Slf4j
public class MsgInfinitySendThread extends Thread {

    private IMsgSender iMsgSender;

    public MsgInfinitySendThread(IMsgSender msgSender) {
        this.iMsgSender = msgSender;
        PushData.activeThreadConcurrentLinkedQueue.offer(this.getName());
        PushData.threadStatusMap.put(this.getName(), true);
    }

    @Override
    public void run() {

        while (PushData.running && PushData.threadStatusMap.get(this.getName()) && !PushData.toSendConcurrentLinkedQueue.isEmpty()) {
            String[] msgData = PushData.toSendConcurrentLinkedQueue.poll();
            if (msgData == null) {
                continue;
            }
            try {
//                SendResult sendResult = iMsgSender.send(msgData);
                SendResult sendResult = new SendResult();
                if (sendResult.isSuccess()) {
                    PushData.increaseSuccess();
                    // 保存发送成功
//                    ConsoleUtil.infinityConsoleOnly(Thread.currentThread().getName() + "：发送成功：" + msgData[0]);
                    PushData.sendSuccessList.add(msgData);
                } else {
                    PushData.increaseFail();
//                    InfinityForm.getInstance().getPushFailCount().setText(String.valueOf(PushData.failRecords));
                    // 保存发送失败
                    PushData.sendFailList.add(msgData);
                    log.info("发送失败:" + sendResult.getInfo() + ";msgData:" + JSONUtil.toJsonPrettyStr(msgData));
                }
            } catch (Exception e) {
                PushData.increaseFail();
//                InfinityForm.getInstance().getPushFailCount().setText(String.valueOf(PushData.failRecords));
                log.info("发送异常：" + ExceptionUtils.getStackTrace(e));
                // 保存发送失败
                PushData.sendFailList.add(msgData);
            }
            // 已处理+1
            PushData.increaseProcessed();
//            InfinityForm.getInstance().getPushSuccessCount().setText(String.valueOf(PushData.successRecords));

            // 总进度条
//            InfinityForm.getInstance().getPushTotalProgressBar().setValue(PushData.processedRecords.intValue());
        }
        PushData.activeThreadConcurrentLinkedQueue.remove(this.getName());
        PushData.threadStatusMap.put(this.getName(), false);

    }
}
