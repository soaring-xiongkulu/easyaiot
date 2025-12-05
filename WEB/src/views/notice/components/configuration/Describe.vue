<template>
  <div class="describe-wapper">
    <Typography>
      <div v-if="noticeType == 'email'">
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph
          >通知配置可以结合通知配置为告警消息通知提供支撑。也可以用于系统中其他自定义模块的调用。</TypographyParagraph
        >
        <TypographyTitle :level="5">2.通知配置说明</TypographyTitle>
        <TypographyParagraph>
          1、 服务器地址<br />
          下拉可选择国内常用的邮箱服务配置，也支持手动输入其他地址。
          系统使用POP协议。POP允许电子邮件客户端下载服务器上的邮件，但是您在电子邮件客户端的操作（如：移动邮件、标记已读等），这时不会反馈到服务器上。
        </TypographyParagraph>
        <TypographyParagraph>
          2、发件人<br />
          用于发送邮件时“发件人“信息的显示
        </TypographyParagraph>
        <TypographyParagraph>
          3、 用户名<br />
          用该账号进行发送邮件。
        </TypographyParagraph>
        <TypographyParagraph>
          4、密码<br />
          用于账号身份认证，认证通过后可通过该账号进行发送邮件。
        </TypographyParagraph>
      </div>
      <div v-if="noticeType == 'sms'">
        <TypographyParagraph>
          <div class="link">阿里云管理控制台：https://home.console.aliyun.com</div>
        </TypographyParagraph>
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph
          >通知配置可以结合通知配置为告警消息通知提供支撑。也可以用于系统中其他自定义模块的调用。</TypographyParagraph
        >
        <TypographyTitle :level="5">2.通知配置说明</TypographyTitle>
        <TypographyParagraph>
          1、RegionID<br />
          阿里云内部给每台机器设置的唯一编号。请根据购买的阿里云服务器地址进行填写。<br />
          阿里云地域和可用区对照表地址：<br />https://help.aliyun.com/document_detail/40654.html?<br />spm=a2c6h.13066369.0.0.54a174710O7rWH
        </TypographyParagraph>
        <TypographyParagraph>
          2、AccesskeyID/Secret<br />
          用于程序通知方式调用云服务费API的用户标识和秘钥<br />
          获取路径：“阿里云管理控制台”--“用户头像”--“”--“AccessKey管理”--“查看”
        </TypographyParagraph>
        <TypographyParagraph>
          <img
            :src="AccesskeyIDSecret"
            width="487"
            @click="handlePreviewImage(AccesskeyIDSecret)"
          />
        </TypographyParagraph>
      </div>
      <div v-if="noticeType == 'weixin'">
        <div class="link">企业微信管理后台：https://work.weixin.qq.com</div>
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph>
          通知配置可以结合通知配置为告警消息通知提供支撑。也可以用于系统中其他自定义模块的调用。
        </TypographyParagraph>
        <TypographyTitle :level="5">2.通知配置说明</TypographyTitle>
        <TypographyParagraph>
          1、corpId<br />
          企业微信的唯一专属编号。<br />
          获取路径：“企业微信”管理后台--“我的企业”--“企业ID”<br />
        </TypographyParagraph>
        <TypographyParagraph>
          <img :src="CorpId" width="487" @click="handlePreviewImage(CorpId)" />
        </TypographyParagraph>
        <TypographyParagraph>
          2、corpSecret<br />
          应用的唯一secret,一个企业微信中可以有多个corpSecret<br />
          获取路径：“企业微信”--“应用与小程序”--“自建应用”中获取<br />
        </TypographyParagraph>
        <TypographyParagraph>
          <img :src="CorpSecret" width="487" @click="handlePreviewImage(CorpSecret)" />
        </TypographyParagraph>
      </div>
      <div v-if="noticeType == 'webhook'">
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph>
          webhook是一个接收HTTP请求的URL（本平台默认只支持HTTP
          POST请求），实现了Webhook的第三方系统可以基于该URL订阅本平台系统信息，本平台按配置把特定的事件结果推送到指定的地址，便于系统做后续处理。
        </TypographyParagraph>
        <TypographyTitle :level="5">2.通知配置说明</TypographyTitle>
        <TypographyParagraph>
          1、Webhook<br />
          Webhook地址。<br />
          2、请求头<br />
          支持根据系统提供的接口设置不同的请求头。如 Accept-Language 、Content-Type<br />
        </TypographyParagraph>
      </div>
    </Typography>
  </div>
</template>

<script lang="ts" setup>
  import { Typography, TypographyTitle, TypographyParagraph } from 'ant-design-vue';
  import { createImgPreview } from '@/components/Preview';
  import { ref } from 'vue';
  import AccesskeyIDSecret from '@/assets/images/AccesskeyIDSecret.a4d4481d.jpg';
  import CorpId from '@/assets/images/CorpId.jpg';
  import CorpSecret from '@/assets/images/CorpSecret.jpg';

  const noticeType = ref('email');

  const handlePreviewImage = (img) => {
    createImgPreview({ imageList: [img] });
  };

  const setNoticeType = (value) => {
    noticeType.value = value;
  };

  defineExpose({
    setNoticeType,
  });
</script>
<style lang="less" scoped>
  .describe-wapper {
    article {
      padding: 24px;
      background-color: #fafafa;
    }

    .link {
      padding: 8px 16px;
      background-color: rgb(167 189 247 / 20%);
      color: #2f54eb;
    }

    img {
      width: 450px;
    }
  }
</style>
