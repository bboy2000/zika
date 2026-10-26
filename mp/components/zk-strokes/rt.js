/**
 * canvas 渲染适配层（P4）
 * 改造自 hanzi-writer-miniprogram@1.1.0 官方 src/RenderTarget.js：
 * 官方版绑定原生组件实例，这里绑定 uni-app Vue 组件实例，其余逻辑一致。
 *
 * 只服务动画（animateCharacter），quiz 的指针事件留空桩（P4 不做屏上书写判定）。
 */

// 微信 canvas 2d 上下文缺 setter，官方版同款补齐
function polyfillCanvasCtx(ctx) {
  ['globalAlpha', 'strokeStyle', 'fillStyle', 'lineWidth', 'lineCap', 'lineJoin'].forEach((setter) => {
    const setterMethod = 'set' + setter[0].toUpperCase() + setter.slice(1)
    Object.defineProperty(ctx, setter, { set: ctx[setterMethod].bind(ctx) })
  })
  return ctx
}

class RT {
  constructor(vm) {
    this.vm = vm
    this.ctx = polyfillCanvasCtx(uni.createCanvasContext('zkstrokes-canvas', vm))
  }

  getContext() {
    return this.ctx
  }

  // —— 指针事件（quiz 专用，P4 动画不需要）——
  addPointerStartListener() {}
  addPointerMoveListener() {}
  addPointerEndListener() {}
  trigger() {}
  removeAllListeners() {}
}

export default {
  init: (vm) => new RT(vm)
}
