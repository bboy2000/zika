<template>
  <view class="tzg" :style="boxStyle">
    <!-- 十字虚线用元素画，不用伪元素（小程序兼容更稳） -->
    <view class="tzg-h"></view>
    <view class="tzg-v"></view>
    <text class="tzg-t" :style="charStyle">{{ char }}</text>
  </view>
</template>

<script>
/**
 * 田字格（DESIGN.md 4.7）
 * P1：静态楷体大字，用于详情弹层展示字形
 * P4：内部换成 canvas 自绘笔顺 + 逐笔累加动画，本组件对外接口（char/size）保持不变
 */
export default {
  name: 'zk-tzg',
  props: {
    char: { type: String, default: '' },
    size: { type: Number, default: 180 }
  },
  computed: {
    boxStyle() {
      return { width: this.size + 'px', height: this.size + 'px' }
    },
    charStyle() {
      // 字占格约 72%，留出四周留白，符合课本占格
      return {
        fontSize: Math.round(this.size * 0.72) + 'px',
        lineHeight: '1'
      }
    }
  }
}
</script>

<style>
.tzg {
  position: relative;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border: 1.5px solid #e0a8a0;
  border-radius: 6px;
  overflow: hidden;
  flex: none;
}
.tzg-h {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  border-top: 1px dashed #e0a8a0;
  opacity: 0.75;
}
.tzg-v {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  border-left: 1px dashed #e0a8a0;
  opacity: 0.75;
}
.tzg-t {
  position: relative;
  z-index: 1;
  text-align: center;
  color: #2b2b2b;
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-weight: 400;
  /* 楷体字形在 em 框内略偏下，上抬 1.5% 让视觉居中 */
  transform: translateY(-1.5%);
}
</style>
