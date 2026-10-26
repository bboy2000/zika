/**
 * canvas 渲染适配层（P4，v0.3.4 改新版 Canvas 2D 接口）
 *
 * v0.3.2/3 用旧接口 uni.createCanvasContext(id, vm) 失败：vendor 未做 $scope
 * 垫片，wx 收到 Vue 代理后组件内 canvas 作用域失效 → 静默画不出。
 * 改用 type="2d" + createSelectorQuery().in(vm)（uni 有官方垫片）拿 node，
 * 得到标准 2d context（无需 polyfill、无需 ctx.draw() 刷新），DPR 自理。
 *
 * quiz 的指针事件留空桩（P4 不做屏上书写判定）。
 */

export default {
  /**
   * 异步初始化：查 canvas node → 设定 DPR 分辨率 → 返回 RT。
   * 失败返回 { ok: false }，由组件降级。
   */
  async init(vm) {
    try {
      const info = await new Promise((resolve) => {
        uni.createSelectorQuery().in(vm)
          .select('#zkstrokes-canvas')
          .fields({ node: true, size: true })
          .exec((r) => resolve(r && r[0]))
      })
      const canvas = info && info.node
      if (!canvas) return { ok: false, getContext() { return null } }

      const dpr = (uni.getSystemInfoSync().pixelRatio) || 2
      const w = info.width || 180
      const h = info.height || 180
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr) // 核心全部用 save/transform/restore 相对变换，基准缩放可保留

      return {
        ok: true,
        getContext: () => ctx,
        // —— 指针事件（quiz 专用，P4 动画不需要）——
        addPointerStartListener() {},
        addPointerMoveListener() {},
        addPointerEndListener() {},
        trigger() {},
        removeAllListeners() {}
      }
    } catch (e) {
      return { ok: false, getContext() { return null } }
    }
  }
}
