<template>
  <view v-if="show" class="zd-root" :class="{ pad: isPad }">
    <view class="zd-mask" @tap="onClose"></view>

    <view class="zd-sheet" :class="isPad ? 'is-pad' : 'is-phone'">
      <!-- head 固定：朱红大字 + 拼音格 + 部首·结构·出处（结构对齐原版 .modal-head） -->
      <view class="zd-head">
        <view class="zd-big">
          <text class="zd-big-t">{{ item.ch }}</text>
        </view>
        <view class="zd-head-r">
          <view class="zd-hrow">
            <view class="zd-py">
              <zk-py :text="item.py" size="md" />
            </view>
            <view class="zd-spk" @tap="$emit('speak')">
              <view class="zd-spk-i"></view>
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
        <view class="zd-close" @tap="onClose">
          <text class="zd-close-i">✕</text>
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

        <!-- 多音字：每个读音独立一组（P2 重建，见 tools/build-multi.py） -->
        <view v-if="multi && multi.length" class="zd-block">
          <view class="zd-block-h">
            <text class="zd-block-t">多音字</text>
            <text class="zd-block-hint">这个字有几个读音</text>
          </view>
          <view class="zd-multi">
            <view
              v-for="(r, ri) in multi"
              :key="ri"
              class="zd-mrow"
              :class="{ on: r.isLesson }"
            >
              <view class="zd-mhead">
                <view class="zd-mpy">
                  <zk-py :text="r.py" size="sm" />
                </view>
                <text v-if="r.isLesson" class="zd-mtag">本课</text>
              </view>
              <view class="zd-mwords">
                <view v-for="(w, wi) in r.words" :key="wi" class="zd-mword">
                  <text class="zd-mword-t">{{ w }}</text>
                </view>
              </view>
              <text v-if="r.from" class="zd-mfrom">{{ r.from }}</text>
            </view>
          </view>
        </view>

        <view v-if="item.defs && item.defs.length" class="zd-block">
          <view class="zd-block-h">
            <text class="zd-block-t">释义</text>
          </view>
          <view class="zd-defs">
            <view v-for="(d, di) in item.defs" :key="di" class="zd-def-row">
              <text v-if="item.defs.length > 1" class="zd-def-no">{{ MARKS[di] || '·' }}</text>
              <text class="zd-def-t">{{ d }}</text>
            </view>
          </view>
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
    item: { type: Object, default: () => ({ ch: '', py: '', words: [], lesson: '', defs: [] }) },
    /** 该字的多音字读音组，空数组表示不是多音字 */
    multi: { type: Array, default: () => [] },
    meta: { type: Object, default: () => ({}) },
    learned: { type: Boolean, default: false },
    inBook: { type: Boolean, default: false },
    isPad: { type: Boolean, default: false },
    canPrev: { type: Boolean, default: false },
    canNext: { type: Boolean, default: false }
  },
  emits: ['close', 'prev', 'next', 'learned', 'wordbook', 'speak'],
  data() {
    return {
      /** 义项序号：圆圈数字比「1.」更贴合课本，最多 4 条（数据层也限 2 条） */
      MARKS: ['①', '②', '③', '④']
    }
  },
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
  align-items: center;
  justify-content: center;
  /* 居中弹窗：四周留白 16px，同原版 #mask。
     居中而不是贴底，是为了不被原生 tabBar 压住底栏按钮。 */
  padding: 16px;
  box-sizing: border-box;
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
  background: #fffdf7;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden; /* 铁律：不加会让内部背景溢出，圆角变直角 */
  animation: zdPop 0.22s ease both;
}
/* 手机与平板同一套结构，只是尺寸不同（原版 #modal 手机 16px 圆角、桌面 20px） */
.zd-sheet.is-phone {
  max-width: 100%;
  max-height: 86%;
  border-radius: 16px;
}
.zd-sheet.is-pad {
  max-width: 520px;
  max-height: 86%;
  border-radius: 20px;
}

/* head：大红字在左，右边一列拼音 + 出处 */
.zd-head {
  flex: none;
  position: relative;
  display: flex;
  align-items: center;
  padding: 18px 18px 12px;
  border-bottom: 1px solid #f0e9d8;
}
.zd-big {
  flex: none;
  width: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-big-t {
  /* flex:none 必须给，否则 text 会被 flex 压窄，字变瘦长 */
  flex: none;
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 60px;
  line-height: 1.1;
  font-weight: 700;
  color: #a3281c;
}
.zd-head-r {
  flex: 1;
  min-width: 0;
  margin-left: 14px;
  padding-right: 34px; /* 给右上角关闭钮让位 */
}
.zd-hrow {
  display: flex;
  align-items: center;
}
.zd-py {
  flex: none;
}
.zd-spk {
  flex: none;
  margin-left: 8px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #fcf2ee;
  border: 1px solid #f0dfbc;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-spk-i {
  width: 14px;
  height: 14px;
  background-repeat: no-repeat;
  background-size: 100% 100%;
  background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHZpZXdCb3g9JzAgMCAyNCAyNCcgZmlsbD0nbm9uZScgc3Ryb2tlPScjQzkzQTJCJyBzdHJva2Utd2lkdGg9JzIuMicgc3Ryb2tlLWxpbmVjYXA9J3JvdW5kJyBzdHJva2UtbGluZWpvaW49J3JvdW5kJz48cGF0aCBkPSdNMTEgNSA2IDlIM3Y2aDNsNSA0VjV6Jy8+PHBhdGggZD0nTTE1LjUgOC41YTUgNSAwIDAgMSAwIDcnLz48cGF0aCBkPSdNMTguNSA1LjVhOSA5IDAgMCAxIDAgMTMnLz48L3N2Zz4=");
}
.zd-root.pad .zd-big {
  width: 74px;
}
.zd-root.pad .zd-big-t {
  font-size: 72px;
}
.zd-root.pad .zd-mword-t {
  font-size: 15px;
}
.zd-root.pad .zd-mfrom {
  font-size: 12px;
}
.zd-close {
  position: absolute;
  top: 10px;
  right: 12px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #c93a2b;
  box-shadow: 0 2px 8px rgba(201, 58, 43, 0.35);
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
  flex-wrap: wrap;
  margin-top: 8px;
}
.zd-meta-i {
  font-size: 12px;
  color: #6b675c;
}
.zd-dot {
  font-size: 12px;
  color: #bdb5a4;
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
  background: #fffdf7;
  border: 1px solid #e6ddc8;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-nav-btn.off {
  opacity: 0.35;
}
.zd-nav-t {
  font-size: 13px;
  color: #6b675c;
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
  color: #6b675c;
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
  background: #f0e9d8;
}
.zd-word-t {
  font-size: 14px;
  color: #6b675c;
}
.zd-empty {
  font-size: 13px;
  color: #a9a296;
}
.zd-block-hint {
  margin-left: 8px;
  font-size: 11px;
  color: #a9a296;
}
/* 多音字：一读音一行的分组卡片，本课读音朱砂淡底高亮 */
.zd-multi {
  border: 1.5px solid #e6ddc8;
  border-radius: 12px;
  overflow: hidden;
  background: #fffdf7;
}
.zd-mrow {
  padding: 10px 12px 8px;
  border-top: 1px dashed #ece3cf;
}
.zd-mrow:first-child {
  border-top: 0;
}
.zd-mrow.on {
  background: #fcf2ee;
}
.zd-mhead {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.zd-mpy {
  margin-right: 8px;
}
.zd-mtag {
  font-size: 10px;
  line-height: 14px;
  padding: 1px 5px;
  border-radius: 3px;
  color: #c93a2b;
  background: #f9e9e4;
  border: 1px solid #f0d5cd;
}
.zd-mwords {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  margin-top: 6px;
}
.zd-mword {
  padding: 3px 9px;
  margin: 0 6px 4px 0;
  border-radius: 999px;
  background: #f7ecd6;
  border: 1px solid #f0dfbc;
}
.zd-mword-t {
  font-size: 13px;
  color: #33322e;
}
.zd-mfrom {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: #a9a296;
}
.zd-defs {
  display: flex;
  flex-direction: column;
}
.zd-def-row {
  display: flex;
  align-items: flex-start;
}
.zd-def-row + .zd-def-row {
  margin-top: 3px;
}
/* 序号只在多条时出现：单条释义加序号是多余装饰 */
.zd-def-no {
  flex: none;
  font-size: 13px;
  line-height: 1.75;
  color: #c93a2b;
  margin-right: 4px;
}
.zd-def-t {
  flex: 1;
  font-size: 13px;
  line-height: 1.75;
  color: #6b675c;
}

/* foot */
.zd-foot {
  flex: none;
  display: flex;
  align-items: center;
  padding: 10px 16px;
  padding-bottom: calc(10px + constant(safe-area-inset-bottom));
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid #f0e9d8;
  background: #fffdf7;
}
.zd-btn-main {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  background: #c9973f;
  box-shadow: 0 4px 14px rgba(242, 178, 48, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-btn-main.done {
  background: #e7f0e6;
  box-shadow: none;
}
.zd-btn-main-t {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}
.zd-btn-main.done .zd-btn-main-t {
  color: #5d8a66;
}
.zd-btn-sub {
  margin-left: 10px;
  padding: 0 14px;
  height: 44px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e6ddc8;
  display: flex;
  align-items: center;
  justify-content: center;
}
.zd-btn-sub.on {
  border-color: #c93a2b;
  background: #fcf2ee;
}
.zd-btn-sub-t {
  font-size: 13px;
  color: #6b675c;
}
.zd-btn-sub.on .zd-btn-sub-t {
  color: #c93a2b;
}

@keyframes zdMaskIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes zdPop {
  from {
    transform: scale(0.94);
    opacity: 0;
  }
  to {
    transform: scale(1);
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
