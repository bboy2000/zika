<template>
  <view class="zkst" :style="boxStyle" @tap="replay">
    <!-- 米字格：与 zk-tzg 同款元素画法（十字暖金 + 对角浅金，渐变画斜线会粗细不匀） -->
    <view class="zkst-h"></view>
    <view class="zkst-v"></view>
    <view class="zkst-d zkst-d1"></view>
    <view class="zkst-d zkst-d2"></view>

    <!-- 小程序：canvas(2d) 透明叠加，只画笔画 -->
    <!-- #ifdef MP-WEIXIN -->
    <canvas
      v-if="!failed"
      id="zkstrokes-canvas"
      type="2d"
      class="zkst-c"
      :style="boxStyle"
    ></canvas>
    <!-- #endif -->

    <!-- 降级：数据失败或 H5 预览 → 静态楷体字（即原 zk-tzg 形态） -->
    <text v-if="failed" class="zkst-t" :style="charStyle">{{ char }}</text>
    <!-- #ifndef MP-WEIXIN -->
    <text class="zkst-t" :style="charStyle">{{ char }}</text>
    <!-- #endif -->
  </view>
</template>

<script>
// #ifdef MP-WEIXIN
import HanziWriter from 'hanzi-writer'
import RT from './rt.js'
// #endif
import { loadStrokes } from '@/common/strokes.js'

/**
 * 笔顺动画米字格（P4）
 *
 * 复用老 Web 版方案（public/index.html playAnimation）：
 * 动态笔顺 = hanzi-writer@3.7.3，参数同款（描边 #33322e / 轮廓 #d8cfb8 / 速 1.1 / 间隔 260）。
 * 米字格规格 = zk-tzg 同款（DESIGN.md 4.7），canvas 透明叠加只画笔画。
 * 数据 = 云存储按字 JSON（common/strokes.js），charDataLoader 喂给 hanzi-writer。
 *
 * 对外接口与 zk-tzg 一致（char/size），详情弹层可直接替换。
 * 点按重播；加载失败降级为静态楷体大字。
 */
export default {
  name: 'zk-strokes',
  props: {
    char: { type: String, default: '' },
    size: { type: Number, default: 180 }
  },
  data() {
    return {
      failed: false
    }
  },
  computed: {
    boxStyle() {
      return { width: this.size + 'px', height: this.size + 'px' }
    },
    charStyle() {
      return {
        fontSize: Math.round(this.size * 0.72) + 'px',
        lineHeight: '1'
      }
    }
  },
  watch: {
    char() {
      this.init()
    }
  },
  mounted() {
    this.init()
  },
  beforeDestroy() {
    this.stop()
  },
  methods: {
    stop() {
      // #ifdef MP-WEIXIN
      if (this.writer) {
        try { this.writer.cancelQuiz() } catch (e) { /* noop */ }
        try { this.writer.hideCharacter() } catch (e) { /* noop */ }
        this.writer = null
      }
      // #endif
    },
    async init() {
      const ch = this.char
      this.stop()
      this.failed = false
      if (!ch) return

      // #ifdef MP-WEIXIN
      try {
        const data = await loadStrokes(ch)
        if (ch !== this.char) return // 弹层已切字，丢弃
        await this.$nextTick() // 确保 canvas 节点已渲染
        const rt = await RT.init(this)
        if (!rt.ok || ch !== this.char) {
          this.failed = true
          return
        }
        this.writer = new HanziWriter({}, {
          width: this.size,
          height: this.size,
          padding: Math.max(4, Math.round(this.size * 0.035)), // 老版 230px/8px 同比例
          charDataLoader: (c, onLoad, onError) => {
            loadStrokes(c)
              .then((d) => onLoad({ strokes: d.s, medians: d.m }))
              .catch(onError)
          },
          showCharacter: false,
          showOutline: true,
          strokeColor: '#33322e',
          outlineColor: '#d8cfb8',
          strokeAnimationSpeed: 1.1,
          delayBetweenStrokes: 260,
          rendererOverride: { createRenderTarget: () => rt },
          renderer: 'canvas'
        })
        // 必须先 setCharacter（老版走 HanziWriter.create 内部自带这步，直接 new 不会自动加载）
        this.writer.setCharacter(ch)
          .then(() => {
            if (ch !== this.char || !this.writer) return
            return this.writer.animateCharacter()
          })
          .catch(() => {
            if (ch === this.char) this.failed = true
          })
      } catch (e) {
        this.failed = true
      }
      // #endif
    },
    replay() {
      // #ifdef MP-WEIXIN
      if (this.writer) {
        try { this.writer.animateCharacter() } catch (e) { /* noop */ }
      }
      // #endif
    }
  }
}
</script>

<style>
.zkst {
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
.zkst-h {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  margin-top: -0.5px;
  background: #d9c69a;
}
.zkst-v {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  margin-left: -0.5px;
  background: #d9c69a;
}
/* 对角线 */
.zkst-d {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 141.42%;
  height: 1px;
  margin-left: -70.71%;
  margin-top: -0.5px;
  background: #efe4c4;
}
.zkst-d1 {
  transform: rotate(45deg);
}
.zkst-d2 {
  transform: rotate(-45deg);
}
/* canvas 透明叠在格上 */
.zkst-c {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 1;
}
/* 静态降级字 */
.zkst-t {
  position: relative;
  z-index: 1;
  text-align: center;
  color: #33322e;
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-weight: 400;
  transform: translateY(-1.5%);
}
</style>
