<template>
  <Card
    ref="cardRef"
    :hoverable="props.hoverable"
    :class="{ 'no-bg': !props.bgUrl }"
    @click="handleClick"
  >
    <div
      v-if="!props.bgUrl"
      class="card-content-bg1"
      :class="{ 'card-content-bg-warn': props.status === 'OFFLINE' }"
    >
    </div>
    <div
      v-if="!props.bgUrl"
      class="card-content-bg2"
      :class="{ 'card-content-bg-warn': props.status === 'OFFLINE' }"
    >
    </div>

    <div v-if="props.isBadge" class="card-state" :class="{ 'card-state-warn': props.status === 'OFFLINE' }">
      <div class="card-state-content">
        <Badge
          :color="props.status === 'ONLINE' ? 'green' : 'red'"
          :text="props.status === 'ONLINE' ? '在线' : '离线'"
        />
      </div>
    </div>

    <slot></slot>
  </Card>
</template>

<script lang="ts" setup name="CustomCard">
  import { Card, Badge } from 'ant-design-vue';
  import { withDefaults, ref, onUnmounted, watchEffect } from 'vue';

  interface Props {
    status?: string;
    isBadge?: boolean;
    bgUrl?: string;
    hoverable?: boolean;
  }

  const props = withDefaults(defineProps<Props>(), {
    status: 1,
    isBadge: false,
    bgUrl: '',
    hoverable: false,
  });

  const emit = defineEmits(['click']);

  const cardRef = ref();

  const handleClick = () => {
    emit('click');
  };

  const stop = watchEffect(() => {
    if (props.bgUrl) {
      if (!cardRef.value) return;
      cardRef.value.$el.style = `background: url(${props.bgUrl}) 0% 0% / 100% 100% no-repeat`;
    }
  });

  onUnmounted(() => {
    stop();
  });
</script>

<style lang="less" scoped>
  .no-bg {
    :deep(.ant-card-body) {
      &::before {
        content: ' ';
        display: block;
        position: absolute;
        top: 0;
        left: 40px;
        width: 15%;
        min-width: 64px;
        height: 2px;
        border-radius: 0 0 3px 3px;
        background-color: #91a1ef;
        // background-image: url(../images/rectangle.png);
        background-repeat: no-repeat;
        background-size: 100% 100%;
      }
    }
  }

  :deep(.ant-card-body) {
    position: relative;
    overflow: hidden;
    cursor: pointer;

    .card-content-bg1,
    .card-content-bg2 {
      position: absolute;
      top: 0;
      right: -5%;
      width: 44.65%;
      height: 100%;
      transform: skew(-15deg);
    }

    .card-content-bg1 {
      background: linear-gradient(188.4deg, rgb(9 46 231 / 3%) 30%, rgb(9 46 231 / 0%) 80%);
    }

    .card-content-bg2 {
      width: calc(44.65% + 34px);
      background: linear-gradient(188.4deg, rgb(9 46 231 / 3%) 30%, rgb(9 46 231 / 0%) 80%);
    }

    .card-content-bg-warn {
      background: linear-gradient(188.4deg, rgb(229 0 18 / 3%) 22.94%, rgb(229 0 18 / 0%) 94.62%);
    }

    .card-state {
      display: flex;
      position: absolute;
      top: 0px;
      right: -12px;
      justify-content: center;
      width: 100px;
      padding: 2px 0;
      transform: skew(45deg);
      background-color: #5995f526;

      &-content {
        transform: skew(-45deg);
      }

      &-warn {
        background-color: rgb(229 0 18 / 10%);
      }
    }
  }
</style>
