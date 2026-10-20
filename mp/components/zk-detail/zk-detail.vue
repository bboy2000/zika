<template>
  <view v-if="show" class="zd-root" :class="{ pad: isPad }">
    <view class="zd-mask" @tap="onClose"></view>

    <view class="zd-sheet" :class="isPad ? 'is-pad' : 'is-phone'">
      <!-- head 固定：拼音格 + 发音 + 关闭 / 部首·结构·出处 -->
      <view class="zd-head">
        <view class="zd-hrow">
          <view class="zd-py">
            <zk-py :text="item.py" size="md" />
          </view>
          <view class="zd-spk" @tap="$emit('speak')">
            <text class="zd-spk-i">♪</text>
          </view>
          <view class="zd-close" @tap="onClose">
            <text class="zd-close-i">✕</text>
          </view>
        </view>
        <view class="zd-meta">
          <text class="zd-meta-i">部首 {{ meta.radical || '—' }}</text>
          <text class="zd-dot">·</text>
          <text class="zd-meta-i">{{ meta.struct || '—' }}</text>
          <text class="zd-dot">·</text>
          <text class="zd-meta-i">{{ item.lesson }}</text>
        </view>
      </view>

      <!-- body 滚动：田字格 → 翻字 → 组词 → 释义 -->
      <scroll-view class="zd-body" scroll-y :show-scrollbar="false">
        <view class="zd-stage">
          <zk-tzg :char="item.ch" :size="isPad ? 250 : 180" />
        </view>

        <view class="zd-nav">
          <view class="zd-nav-btn" :class="{ off: !canPrev }" @tap="onPrev">
            <text class="zd-nav-t">‹ 上一字</text>
          </view>
          <view class="zd-nav-btn" :class="{ off: !canNext }" @tap="onNext">
            <text class="zd-nav-t">下一字 ›</text>
          </view>
        </view>

        <view class="zd-block">
          <view class="zd-block-h">
            <text class="zd-block-t">组词</text>
          </view>
          <view class="zd-words">
            <view v-for="(w, i) in item.words" :key="i" class="zd-word">
              <text class="zd-word-t">{{ w }}</text>
            </view>
            <text v-if="!item.words || !item.words.length" class="zd-empty">暂无组词</text>
          </view>
        </view>

        <view v-if="item.exp" class="zd-block">
          <view class="zd-block-h">
            <text class="zd-block-t">释义</text>
          </view>
          <text class="zd-exp">{{ item.exp }}</text>
        </view>
      </scroll-view>

      <!-- foot 固定：激励动作永远可见 -->
      <view class="zd-foot">
        <view class="zd-btn-main" :class="{ done: learned }" @tap="$emit('learned')">
          <text class="zd-btn-main-t">{{ learned ? '已学会 ✓' : '学会啦 +1★' }}</text>
        </view>
        <view class="zd-btn-sub" :class="{ on: inBook }" @tap="$emit('wordbook')">
          <text class="zd-btn-sub-t">{{ inBook ? '已在生字本' : '加入生字本' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import zkPy from '@/components/zk-py/zk-py.vue'
import zkTzg from '@/components/zk-tzg/zk-tzg.vue'

/**
 * 字卡详情弹层（DESIGN.md 5.5）
 *
 * 为什么整块做成组件而不是"容器组件 + slot"：
 * 小程序自定义组件默认样式隔离，页面里写的类名对 slot 内容不生效，
 * 弹层会变成一坨无样式内容。把结构与样式一起收进来，隔离问题不存在，
 * 搜索页（P7）也能直接复用。
 *
 * 手机底部滑出 / 平板居中限宽 560，一套结构两端通用，不做左右分栏。
 */
export default {
  name: 'zk-detail',
  components: { zkPy, zkTzg },
  props: {
    show: { type: Boolean, default: false },
    item: { type: Object, default: () => ({ ch: '', py: '', words: [], lesson: '', exp: '' }) },
    meta: { type: Object, default: () => ({}) },
    learned: { type: Boolean, default: false },
    inBook: { type: Boolean, default: false },
    isPad: { type: Boolean, default: false },
    canPrev: { type: Boolean, default: false },
    canNext: { type: Boolean, default: false }
  },
  emits: ['close', 'prev', 'next', 'learned', 'wordbook', 'speak'],
  methods: {
    onClose() {
      this.$emit('close')
    },
    onPrev() {
      if (this.canPrev) this.$emit('prev')
    },
    onNext() {
      if (this.canNext) this.$emit('next')
    }
  }
}
</script>

<style>
.zd-root {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 900;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.zd-root.pad {
  align-items: center;
}

.zd-mask {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(34, 31, 28, 0.42);
  animation: zdMaskIn 0.18s ease both;
}

.zd-sheet {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  background: #ffffff;
  overflow: hidden; /* 铁律：不加会让内部背景溢出，平板圆角变直角 */
}
.zd-sheet.is-phone {
  max-height: 94%;
  border-radius: 20px 20px 0 0;
  animation: zdUp 0.22s cubic-bezier(0.22, 0.9, 0.3, 1) both;
}
.zd-sheet.is-pad {
  max-width: 560px;
  max-height: 86%;
  border-radius: 24px;
  animation: zdIn 0.24s cubic-bezier(0.22, 0.9, 0.3, 1) both;
}

/* head */
.zd-head {
  flex: none;
  padding: 16px 16px 12px;
  border-bottom: 1px solid #f5efe5;
}
.zd-hrow {
  display: flex;
  align-items: center;
}
.zd-py {
  min-width: 46px;
}
.zd-spk {
  margin-left: 10px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #fdf3f0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-spk-i {
  font-size: 14px;
  line-height: 14px;
  color: #d94f3d;
}
.zd-close {
  margin-left: auto;
  width: 29px;
  height: 29px;
  border-radius: 50%;
  background: #d94f3d;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-close-i {
  font-size: 14px;
  line-height: 14px;
  color: #ffffff;
}
.zd-meta {
  display: flex;
  align-items: center;
  margin-top: 8px;
}
.zd-meta-i {
  font-size: 12px;
  color: #8a8378;
}
.zd-dot {
  font-size: 12px;
  color: #d8d1c6;
  margin: 0 6px;
}

/* body */
.zd-body {
  flex: 1;
  height: 0; /* 配合 flex:1 让 scroll-view 真正可滚 */
  padding: 16px;
  box-sizing: border-box;
}
.zd-stage {
  display: flex;
  justify-content: center;
  padding: 4px 0 14px;
}
.zd-nav {
  display: flex;
  margin: 0 -4px;
}
.zd-nav-btn {
  flex: 1;
  height: 38px;
  margin: 0 4px;
  border-radius: 10px;
  background: #fbf7f0;
  border: 1px solid #f0e9dd;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-nav-btn.off {
  opacity: 0.35;
}
.zd-nav-t {
  font-size: 13px;
  color: #5c574f;
}

.zd-block {
  margin-top: 16px;
}
.zd-block-h {
  margin-bottom: 8px;
}
.zd-block-t {
  font-size: 12px;
  font-weight: 600;
  color: #8a8378;
  letter-spacing: 1px;
}
.zd-words {
  display: flex;
  flex-wrap: wrap;
}
.zd-word {
  padding: 6px 12px;
  margin: 0 8px 8px 0;
  border-radius: 999px;
  background: #f7f2ea;
}
.zd-word-t {
  font-size: 14px;
  color: #5c574f;
}
.zd-empty {
  font-size: 13px;
  color: #b5aea2;
}
.zd-exp {
  font-size: 13px;
  line-height: 1.75;
  color: #5c574f;
}

/* foot */
.zd-foot {
  flex: none;
  display: flex;
  align-items: center;
  padding: 10px 16px;
  padding-bottom: calc(10px + constant(safe-area-inset-bottom));
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid #f5efe5;
  background: #fffdfa;
}
.zd-btn-main {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  background: #f2b230;
  box-shadow: 0 4px 14px rgba(242, 178, 48, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-btn-main.done {
  background: #e8f4f0;
  box-shadow: none;
}
.zd-btn-main-t {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}
.zd-btn-main.done .zd-btn-main-t {
  color: #57a88f;
}
.zd-btn-sub {
  margin-left: 10px;
  padding: 0 14px;
  height: 44px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #ede6da;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-btn-sub.on {
  border-color: #d94f3d;
  background: #fdf3f0;
}
.zd-btn-sub-t {
  font-size: 13px;
  color: #5c574f;
}
.zd-btn-sub.on .zd-btn-sub-t {
  color: #d94f3d;
}

@keyframes zdMaskIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes zdUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
@keyframes zdIn {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
