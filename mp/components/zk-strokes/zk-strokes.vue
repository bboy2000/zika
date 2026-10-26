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

    <!-- 诊断读数（v0.3.5 临时） -->
    <text v-if="dbg" class="zkst-dbg">{{ dbg }}</text>
  </view>
</template>

<script>
// #ifdef MP-WEIXIN
import HanziWriter from 'hanzi-writer'
import RT from './rt.js'
// #endif
import { loadStrokes } from '@/common/strokes.js'
import { APP_VERSION } from '@/common/version.js'

/**
 * 笔顺动画米字格（P4）
 *
 * 复用老 Web 版方案（public/index.html playAnimation）：
 * 动态笔顺 = hanzi-writer，参数同款（描边 #33322e / 轮廓 #d8cfb8 / 速 1.1 / 间隔 260）。
 * 米字格规格 = zk-tzg 同款（DESIGN.md 4.7），canvas 透明叠加只画笔画。
 *
 * ⚠️ 版本必须锁 2.0.4，不能升 3.x（也已锁在 package.json）：
 *    3.x 的 canvas 渲染器用 `new Path2D(笔画路径)` 画描边，而微信小程序 Canvas 2D
 *    不提供 Path2D，初始化时直接抛 ReferenceError: Path2D is not defined，
 *    结果是画布被 clearRect 清空后一笔都画不出来（表现为「米字格在、字是空的」）。
 *    2.x 有降级分支 `if (usePath2D && global.Path2D) … else pathStringToCanvas(...)`，
 *    官方小程序移植版 hanzi-writer-miniprogram 也是依赖 ^2.0.4，就是同一个原因。
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
      failed: false,
      // 初值即版本指纹：能看到这行说明跑的是本次产物
      dbg: APP_VERSION + ' 待初始化'
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
        this.dbg = APP_VERSION + ' 1 读数据'
        const data = await loadStrokes(ch)
        if (ch !== this.char) return // 弹层已切字，丢弃
        this.dbg = APP_VERSION + ' 2 数据ok ' + (data && data.n ? data.n.length : 0) + '笔'
        await this.$nextTick() // 确保 canvas 节点已渲染
        const rt = await RT.init(this)
        if (!rt.ok) {
          this.dbg = APP_VERSION + ' X 画布 ' + (rt.why || '')
          this.failed = true
          return
        }
        if (ch !== this.char) return
        this.dbg = APP_VERSION + ' 3 画布' + rt.w + 'x' + rt.h + '@' + rt.dpr
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
            if (ch !== this.char || !this.writer) return null
            // === v0.3.8 自检：装字已完成（首帧轮廓已画），立刻补画红块并读回像素 ===
            // 像素读到红色 → 绘制确实进了画布缓冲区，看不见就是显示层问题
            // 像素全 0 → 绘制没落到缓冲区，问题在 ctx/画布绑定
            let pix = 'na'
            try {
              const c0 = rt.getContext()
              const W = Math.round(rt.w * rt.dpr)
              const H = Math.round(rt.h * rt.dpr)
              c0.save()
              c0.setTransform(1, 0, 0, 1, 0, 0) // 复位成设备像素坐标，和 hanzi-writer 的变换解耦
              c0.fillStyle = '#ff0000'
              c0.fillRect(Math.round(W / 2) - 20, Math.round(H / 2) - 20, 40, 40)
              c0.restore()
              try {
                const d = c0.getImageData(Math.round(W / 2), Math.round(H / 2), 1, 1).data
                pix = d[0] + ',' + d[1] + ',' + d[2] + ',' + d[3]
              } catch (e2) {
                pix = 'noGID'
              }
            } catch (e) {
              pix = 'drawE:' + (e && (e.errMsg || e.message))
            }
            this.dbg = APP_VERSION + ' 4 字已装 P:' + pix
            // 停 3 秒让红块可见，再启动动画（动画首帧会 clearRect 清掉红块）
            const my = this._seq = (this._seq || 0) + 1
            setTimeout(() => {
              if (my !== this._seq || ch !== this.char || !this.writer) return
              const p = this.writer.animateCharacter()
              this.dbg = APP_VERSION + ' 5 动画已启动'
              if (p && p.catch) p.catch((e) => { this.dbg = APP_VERSION + ' E动画 ' + (e && (e.errMsg || e.message)) })
            }, 3000)
            return null
          })
          .catch((e) => {
            this.dbg = APP_VERSION + ' E装字 ' + (e && (e.errMsg || e.message || e))
            if (ch === this.char) this.failed = true
          })
      } catch (e) {
        this.dbg = APP_VERSION + ' E初始化 ' + (e && (e.errMsg || e.message || e))
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
/* 诊断读数（v0.3.5 临时） */
.zkst-dbg {
  position: absolute;
  left: 2px;
  right: 2px;
  bottom: 2px;
  z-index: 5;
  font-size: 10px;
  line-height: 1.25;
  color: #C93A2B;
  text-align: center;
  background: rgba(255, 255, 255, 0.88);
  border-radius: 4px;
  padding: 1px 2px;
  word-break: break-all;
}
</style>
