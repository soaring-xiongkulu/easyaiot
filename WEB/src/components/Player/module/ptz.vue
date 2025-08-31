<template>
  <div class="ptz-wrapper" style="display: flex; justify-content: space-around;">
    <div class="control-wrapper">
      <div class="control-btn control-top" @mousedown="ptzCamera('UP')"
           @mouseup="ptzCamera('STOP')">
        <Icon icon="material-symbols:arrows-more-up-rounded"/>
        <div class="control-inner-btn control-inner"></div>
      </div>
      <div class="control-btn control-left" @mousedown="ptzCamera('LEFT')"
           @mouseup="ptzCamera('STOP')">
        <Icon icon="material-symbols:arrows-more-down"/>
        <div class="control-inner-btn control-inner"></div>
      </div>
      <div class="control-btn control-bottom" @mousedown="ptzCamera('DOWN')"
           @mouseup="ptzCamera('STOP')">
        <Icon icon="material-symbols:arrows-more-up-rounded"/>
        <div class="control-inner-btn control-inner"></div>
      </div>
      <div class="control-btn control-right" @mousedown="ptzCamera('RIGHT')"
           @mouseup="ptzCamera('STOP')">
        <Icon icon="material-symbols:arrows-more-up-rounded"/>
        <div class="control-inner-btn control-inner"></div>
      </div>
      <div class="control-round">
        <div class="control-round-inner">
          <Icon icon="material-symbols:pause-circle"/>
        </div>
      </div>
      <div style="position: absolute; left: 7.25rem; top: 1.25rem;"><i
        class="el-icon-zoom-in control-zoom-btn" style="font-size: 1.875rem;"></i></div>
      <div style="position: absolute; left: 7.25rem; top: 3.25rem; font-size: 1.875rem;"><i
        class="el-icon-zoom-out control-zoom-btn"></i></div>
      <div class="contro-speed" style="position: absolute; left: 4px; top: 7rem; width: 9rem;">
        <div role="slider" aria-valuemin="0" aria-valuemax="255" aria-orientation="horizontal"
             class="el-slider" aria-valuetext="30" aria-label="slider between 0 and 255">
          <div class="el-slider__runway">
            <div class="el-slider__bar" style="width: 11.7647%; left: 0%;"></div>
            <div tabindex="0" class="el-slider__button-wrapper" style="left: 11.7647%;">
              <div class="el-tooltip el-slider__button" aria-describedby="el-tooltip-7640"
                   tabindex="0"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import {reactive, ref} from 'vue'
import {Icon} from "@/components/Icon";

const state = reactive({
  numberValue: 0,
})

const emit = defineEmits(['ptzCamera'])
const speed = ref<number>(30)
const ptzCamera = (command) => {
  emit('ptzCamera', command, speed.value)
}
</script>

<style>
.ptz-wrapper {

  .control-wrapper {

    position: relative;
    width: 6.25rem;
    height: 6.25rem;
    max-width: 6.25rem;
    max-height: 6.25rem;
    border-radius: 100%;
    margin: 1.5rem;
    float: left;

    .control-top {
      top: -8%;
      left: 27%;
      -webkit-transform: rotate(-45deg);
      transform: rotate(-45deg);
      border-radius: 5px 100% 5px 0;

      & i {
        -webkit-transform: rotate(45deg);
        transform: rotate(45deg);
        border-radius: 5px 100% 5px 0;
      }

      & .control-inner {
        left: -1px;
        bottom: 0;
        border-top: 1px solid #78aee4;
        border-right: 1px solid #78aee4;
        border-radius: 0 100% 0 0;
      }

      .control-inner-btn {
        position: absolute;
        width: 60%;
        height: 60%;
        background: #fafafa;
      }

      & svg {
        color: #78aee4;
        width: 22px;
        height: 22px;
      }
    }

    .control-left {
      top: 27%;
      left: -8%;
      -webkit-transform: rotate(45deg);
      transform: rotate(45deg);
      border-radius: 5px 0 5px 100%;

      & .control-inner {
        right: -1px;
        top: -1px;
        border-bottom: 1px solid #78aee4;
        border-left: 1px solid #78aee4;
        border-radius: 0 0 0 100%;
      }

      .control-inner-btn {
        position: absolute;
        width: 60%;
        height: 60%;
        background: #fafafa;
      }

      & svg {
        color: #78aee4;
        width: 22px;
        height: 22px;
      }
    }

    .control-bottom {
      left: 27%;
      bottom: -8%;
      -webkit-transform: rotate(45deg);
      transform: rotate(45deg);
      border-radius: 0 5px 100% 5px;

      & span {
        transform: rotate(90deg);
      }

      & i {
        -webkit-transform: rotate(-45deg);
        transform: rotate(-45deg);
      }

      & .control-inner {
        top: -1px;
        left: -1px;
        border-bottom: 1px solid #78aee4;
        border-right: 1px solid #78aee4;
        border-radius: 0 0 100% 0;
      }

      .control-inner-btn {
        position: absolute;
        width: 60%;
        height: 60%;
        background: #fafafa;
      }

      & svg {
        color: #78aee4;
        width: 22px;
        height: 22px;
      }
    }

    .control-right {
      top: 27%;
      right: -8%;
      -webkit-transform: rotate(45deg);
      transform: rotate(45deg);
      border-radius: 5px 100% 5px 0;

      & i {
        -webkit-transform: rotate(-45deg);
        transform: rotate(-45deg);
      }

      & .control-inner {
        left: -1px;
        bottom: -1px;
        border-top: 1px solid #78aee4;
        border-right: 1px solid #78aee4;
        border-radius: 0 100% 0 0;
      }

      .control-inner-btn {
        position: absolute;
        width: 60%;
        height: 60%;
        background: #fafafa;
      }

      & svg {
        color: #78aee4;
        width: 22px;
        height: 22px;
      }
    }

    .control-round {
      position: absolute;
      top: 21%;
      left: 21%;
      width: 58%;
      height: 58%;
      background: #fff;
      border-radius: 100%;
      cursor: pointer;

      .control-round-inner {
        position: absolute;
        left: 13%;
        top: 13%;
        display: -webkit-box;
        display: -ms-flexbox;
        display: flex;
        -webkit-box-pack: center;
        -ms-flex-pack: center;
        justify-content: center;
        -webkit-box-align: center;
        -ms-flex-align: center;
        align-items: center;
        width: 70%;
        height: 70%;
        font-size: 2.5rem;
        color: #78aee4;
        border: 1px solid #78aee4;
        border-radius: 100%;
        -webkit-transition: all 0.3s linear;
        transition: all 0.3s linear;

        & svg {
          width: 40px;
          height: 40px;
        }
      }

      .fa {
        display: inline-block;
        font: normal normal normal 14px / 1 FontAwesome;
        font-size: inherit;
        text-rendering: auto;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }
    }

    .control-btn {
      display: -webkit-box;
      display: -ms-flexbox;
      display: flex;
      -webkit-box-pack: center;
      -ms-flex-pack: center;
      justify-content: center;
      position: absolute;
      width: 44%;
      height: 44%;
      border-radius: 5px;
      border: 1px solid #78aee4;
      -webkit-box-sizing: border-box;
      box-sizing: border-box;
      -webkit-transition: all 0.3s linear;
      transition: all 0.3s linear;
      cursor: pointer;

      & i {
        font-size: 1.25rem;
        color: #78aee4;
        display: -webkit-box;
        display: -ms-flexbox;
        display: flex;
        -webkit-box-pack: center;
        -ms-flex-pack: center;
        justify-content: center;
        -webkit-box-align: center;
        -ms-flex-align: center;
        align-items: center;
      }
    }
  }

  .control-panel {
    position: relative;
    top: 0;
    left: 5rem;
    height: 11rem;
    max-height: 11rem;

    .el-button-group {
      display: inline-block;
      vertical-align: middle;

      &::before {
        display: table;
      }

      .el-tag--medium {
        height: 28px;
        line-height: 26px;
      }

      .el-tag {
        background-color: #ecf5ff;
        border-color: #d9ecff;
        height: 32px;
        padding: 0 10px;
        line-height: 30px;
        font-size: 0.75rem;
        color: #409EFF;
        border-width: 1px;
        border-style: solid;
        border-radius: 4px;
        -webkit-box-sizing: border-box;
        box-sizing: border-box;
        white-space: nowrap;
      }

      .el-input-number--mini {
        width: 130px;
        line-height: 26px;

        .el-input-number__decrease, .el-input-number--mini .el-input-number__increase {
          width: 28px;
          font-size: 0.75rem;
        }

        .el-input-number__decrease.is-disabled, .el-input-number__increase.is-disabled {
          color: #C0C4CC;
          cursor: not-allowed;
        }

        .el-input-number__decrease {
          left: 1px;
          border-radius: 4px 0 0 4px;
          border-right: 1px solid #DCDFE6;
        }

        .el-input-number__decrease, .el-input-number__increase {
          position: absolute;
          z-index: 1;
          top: 1px;
          width: 40px;
          height: auto;
          text-align: center;
          background: #F5F7FA;
          color: #606266;
          cursor: pointer;
          font-size: 0.8125rem;
        }
      }

      .el-input-number {
        position: relative;
        display: inline-block;
        width: 180px;
        line-height: 38px;

        &.is-controls-right .el-input-number__decrease {
          right: 1px;
          bottom: 1px;
          top: auto;
          left: auto;
          border-right: none;
          border-left: 1px solid #DCDFE6;
          border-radius: 0 0 4px;
        }

        &.is-controls-right .el-input-number__increase {
          border-radius: 0 4px 0 0;
          border-bottom: 1px solid #DCDFE6;
        }

        &.is-controls-right .el-input__inner {
          padding-left: 15px;
          padding-right: 50px;
        }

        .el-input {
          display: block;

          .el-input__inner {
            -webkit-appearance: none;
            background-color: #FFF;
            background-image: none;
            border-radius: 4px;
            border: 1px solid #DCDFE6;
            -webkit-box-sizing: border-box;
            box-sizing: border-box;
            color: #606266;
            display: inline-block;
            height: 32px;
            line-height: 32px;
            outline: 0;
            padding: 0 15px;
            -webkit-transition: border-color .2s cubic-bezier(.645, .045, .355, 1);
            transition: border-color .2s cubic-bezier(.645, .045, .355, 1);
            width: 100%;
          }
        }

        .el-input--mini {
          font-size: 0.75rem;
        }
      }

      & > .el-button:not(:first-child):not(:last-child) {
        border-radius: 0;
      }

      & > .el-button:not(:last-child), .el-tabs--left .el-tabs__nav-wrap.is-left {
        margin-right: -1px;
      }

      & > .el-button {
        float: left;
        position: relative;
      }

      .el-button--mini {
        font-size: 0.75rem;
        border-radius: 3px;
      }

      .el-button--mini, .el-button--mini.is-round {
        padding: 7px 15px;
      }

      .el-button {
        display: inline-block;
        line-height: 1;
        white-space: nowrap;
        cursor: pointer;
        background: #FFF;
        border: 1px solid #DCDFE6;
        color: #606266;
        -webkit-appearance: none;
        text-align: center;
        -webkit-box-sizing: border-box;
        box-sizing: border-box;
        outline: 0;
        margin: 0;
        -webkit-transition: .1s;
        transition: .1s;
        font-weight: 500;
        padding: 12px 20px;
        font-size: 0.875rem;
        border-radius: 4px;

        [class*=el-icon-] + span {
          margin-left: 5px;
        }
      }
    }
  }
}

</style>
