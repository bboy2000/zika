/**
 * canvas 渲染适配层（P4，v0.3.5 增加诊断信息）
 *
 * 用 type="2d" + createSelectorQuery().in(vm) 拿 node（uni 对该查询有 vm→$scope 垫片），
 * 得到标准 2d context，DPR 自理。
 * 与 v0.3.4 唯一差别：额外返回 w/h/node 供组件画诊断测试十字。
 */

export default {
  async init(vm) {
    try {
      const info = await new Promise((resolve) => {
        uni.createSelectorQuery().in(vm)
          .select('#zkstrokes-canvas')
          .fields({ node: true, size: true })
          .exec((r) => resolve(r && r[0]))
      })
      const canvas = info && info.node
      if (!canvas) return { ok: false, why: 'node null', getContext() { return null } }

      const dpr = (uni.getSystemInfoSync().pixelRatio) || 2
      const w = info.width || 180
      const h = info.height || 180
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
      const ctx = canvas.getContext('2d')
      if (!ctx) return { ok: false, why: 'ctx null', getContext() { return null } }
      ctx.scale(dpr, dpr) // 核心全用相对变换（save/transform/restore），基准缩放保留

      return {
        ok: true,
        w,
        h,
        dpr,
        node: canvas,
        getContext: () => ctx,
        addPointerStartListener() {},
        addPointerMoveListener() {},
        addPointerEndListener() {},
        trigger() {},
        removeAllListeners() {}
      }
    } catch (e) {
      return { ok: false, why: 'E:' + (e && (e.errMsg || e.message)), getContext() { return null } }
    }
  }
}
