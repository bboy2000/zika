<template>
  <view class="tzg" :style="boxStyle">
    <!-- 米字格：十字 + 两条对角线，全部用元素画（渐变画斜线会粗细不匀） -->
    <view class="tzg-h"></view>
    <view class="tzg-v"></view>
    <view class="tzg-d tzg-d1"></view>
    <view class="tzg-d tzg-d2"></view>
    <text class="tzg-t" :style="charStyle">{{ char }}</text>
  </view>
</template>

<script>
/**
 * 米字格（DESIGN.md 4.7，形态对齐 Web 版 #writerBox）
 * 十字暖金实线 #D9C69A + 对角浅金实线 #EFE4C4，纸底 #FFFEF8
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
  background: #fffef8;
  border: 1.5px solid #dfd0ab;
  border-radius: 12px;
  overflow: hidden;
  flex: none;
}
/* 十字 */
.tzg-h {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  margin-top: -0.5px;
  background: #d9c69a;
}
.tzg-v {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  margin-left: -0.5px;
  background: #d9c69a;
}
/* 对角线：长度 = 格宽 × √2，绕中心旋转 */
.tzg-d {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 141.42%;
  height: 1px;
  margin-left: -70.71%;
  margin-top: -0.5px;
  background: #efe4c4;
}
.tzg-d1 {
  transform: rotate(45deg);
}
.tzg-d2 {
  transform: rotate(-45deg);
}
.tzg-t {
  position: relative;
  z-index: 1;
  text-align: center;
  color: #33322e;
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-weight: 400;
  /* 楷体字形在 em 框内略偏下，上抬 1.5% 让视觉居中 */
  transform: translateY(-1.5%);
}
</style>
