package com.basiclab.iot.message.sendlogic.msgthread;


import com.basiclab.iot.message.sendlogic.PushData;
import com.basiclab.iot.message.sendlogic.msgsender.IMsgSender;

/**
 * 消息异步发送服务线程
 */
public class MsgAsyncSendThread extends Thread {

    private IMsgSender iMsgSender;

    public MsgAsyncSendThread(IMsgSender msgSender) {
        this.iMsgSender = msgSender;
    }

    @Override
    public void run() {

        for (int i = 0; i < PushData.toSendList.size(); i++) {
            if (!PushData.running) {
                PushData.TO_SEND_COUNT.set(i);
                return;
            }
            // 本条消息所需的数据
            String[] msgData = PushData.toSendList.get(i);
            iMsgSender.asyncSend(msgData);
            // 已处理+1
            PushData.increaseProcessed();
//            BoostForm.getInstance().getProcessedCountLabel().setText(String.valueOf(PushData.processedRecords));
//
//            // 总进度条
//            BoostForm.getInstance().getProcessedProgressBar().setValue(PushData.processedRecords.intValue());
        }

    }
}
