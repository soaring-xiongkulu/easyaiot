<template>
  <div class="describe-wapper">
    <Typography>
      <div v-if="noticeType == 'email'">
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph
          >通知模板结合通知配置为告警消息通知提供支撑。通知模板只能调用同一类型的通知配置服务。
          服务器地址支持自定义输入。
        </TypographyParagraph>
        <TypographyTitle :level="5">2.模板配置说明</TypographyTitle>
        <TypographyParagraph>
          1、标题<br />
          支持输入变量，变量格式${标题}
        </TypographyParagraph>
        <TypographyParagraph>
          2、收件人<br />
          支持录入多个邮箱地址，可填写变量参数。
        </TypographyParagraph>
        <TypographyParagraph>
          3、模板内容<br />
          支持填写带变量的动态模板。变量填写规范示例：${name}。填写动态参数后，可对变量的名称、类型、格式进行配置，以便告警通知时填写。
        </TypographyParagraph>
      </div>
      <div v-if="noticeType == 'sms'">
        <TypographyParagraph>
          <div class="link">阿里云管理控制台：https://home.console.aliyun.com</div>
        </TypographyParagraph>
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph
          >通知模板结合通知配置为告警消息通知提供支撑。通知模板只能调用同一类型的通知配置服务。
          使用阿里云短信时需先在阿里云短信服务平台创建短信模板。
        </TypographyParagraph>
        <TypographyTitle :level="5">2.模板配置说明</TypographyTitle>
        <TypographyParagraph>
          1、绑定配置<br />
          使用固定的通知配置发送此通知模板
        </TypographyParagraph>
        <TypographyParagraph>
          2、模板<br />
          阿里云短信平台自定义的模板名称
        </TypographyParagraph>
        <TypographyParagraph>
          3、收信人<br />
          当前仅支持国内手机号，此处若不填，则在模板调试和配置告警通知时手动填写
        </TypographyParagraph>
        <TypographyParagraph>
          4、签名<br />
          用于短信内容签名信息显示，需在阿里云短信进行配置。
        </TypographyParagraph>
        <TypographyParagraph>
          5、变量属性<br />
          需要在当前页面手动设置与阿里云短信模板中一样的变量，否则会导致发送异常。
        </TypographyParagraph>
      </div>
      <div v-if="noticeType == 'weixin'">
        <div class="link">企业微信管理后台：https://work.weixin.qq.com</div>
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph>
          通知模板结合通知配置为告警消息通知提供支撑。通知模板只能调用同一类型的通知配置服务。
        </TypographyParagraph>
        <TypographyTitle :level="5">2.模版配置说明</TypographyTitle>
        <TypographyParagraph>
          1、绑定配置<br />
          使用固定的通知配置发送此通知模板<br />
          2、Agentid<br />
          应用唯一标识<br />
          获取路径：“企业微信”管理后台--“应用管理”--“应用”--“查看应用”<br />
        </TypographyParagraph>
        <TypographyParagraph>
          <img :src="Agentid" width="487" @click="handlePreviewImage(Agentid)" />
        </TypographyParagraph>
        <TypographyParagraph>
          3、收信人ID、收信部门ID、标签推送<br />
          接收通知的3种方式，3个字段若在此页面都没有填写，则在模板调试和配置告警通知时需要手动填写<br />
          收信人ID获取路径：【通讯录】->【成员信息】查看成员账号<br />
          收信组织ID获取路径：【通讯录】->【部门信息】查看部门ID<br />
        </TypographyParagraph>
        <TypographyParagraph>
          <img :src="userID" width="487" @click="handlePreviewImage(userID)" />
        </TypographyParagraph>
        <TypographyParagraph>
          <img :src="toDept" width="487" @click="handlePreviewImage(toDept)" />
        </TypographyParagraph>
        <TypographyParagraph>
          <img :src="toTags" width="487" @click="handlePreviewImage(toTags)" />
        </TypographyParagraph>
      </div>
      <div v-if="noticeType == 'webhook'">
        <TypographyTitle :level="5">1. 概述</TypographyTitle>
        <TypographyParagraph>
          通知模板结合通知配置为告警消息通知提供支撑。通知模板只能调用同一类型的通知配置服务。
        </TypographyParagraph>
        <TypographyTitle :level="5">2.模板配置说明</TypographyTitle>
        <TypographyParagraph>
          1、请求体 请求体中的数据来自于发送通知时指定的所有变量,也可通过自定义的方式进行变量配置。
          使用webhook通知时，系统会将该事件通过您指定的URL地址，以POST方式发送。<br />
        </TypographyParagraph>
      </div>
    </Typography>
  </div>
</template>

<script lang="ts" setup>
  import { Typography, TypographyTitle, TypographyParagraph } from 'ant-design-vue';
  import { ref } from 'vue';
  import { createImgPreview } from '/@/components/Preview/index';
  import Agentid from '@/assets/images/Agentid.jpg';
  import userID from '@/assets/images/userID.jpg';
  import toDept from '@/assets/images/toDept.jpg';
  import toTags from '@/assets/images/toTags.jpg';

  const noticeType = ref('email');

  const setNoticeType = (value) => {
    noticeType.value = value;
  };

  const handlePreviewImage = (img) => {
    createImgPreview({ imageList: [img] });
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
