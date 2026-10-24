<template>
  <view class="page" :class="{ pad: isPad }">
    <!-- 品牌区：朱砂印章 + 衬线标题（原版 header 的手机版形态） -->
    <view class="brand">
      <view class="seal"><text class="seal-t">字</text></view>
      <view class="brand-txt">
        <text class="brand-h1">小学1-6年级写字表字卡</text>
        <text class="brand-sub">统编语文 · 拼音 · 组词 · 笔顺</text>
      </view>
      <view class="stat">
        <text class="stat-s">★</text>
        <text class="stat-n">{{ learnedCount }}</text>
        <text class="stat-t">/{{ curBook ? curBook.charCount : 0 }}</text>
      </view>
    </view>

    <!-- 控制区：册次 + 跳课（胶囊下拉，同原版 select 外观） -->
    <view class="controls">
      <picker mode="selector" :range="bookLabels" :value="bookIndex" @change="onBookPick">
        <view class="sel">
          <text class="sel-t">{{ curBook ? '统编版语文' + curBook.label : '加载中' }}</text>
          <text class="sel-caret">▾</text>
        </view>
      </picker>
      <picker mode="selector" :range="jumpLabels" @change="onJumpPick">
        <view class="sel sel-jump">
          <text class="sel-t">跳转到课程…</text>
          <text class="sel-caret">▾</text>
        </view>
      </picker>
    </view>

    <view class="tip">
      点<text class="tip-b">喇叭</text>朗读读音与组词；点字卡查看<text class="tip-b">笔顺</text>与组词；共<text class="tip-b">{{ curBook ? curBook.charCount : 0 }}</text>个汉字。
    </view>

    <!-- 列表：按课分组 -->
    <view v-if="loading" class="hint">正在打开课本…</view>
    <view v-else-if="errorMsg" class="hint">{{ errorMsg }}</view>
    <view v-else class="lessons">
      <view v-for="(ls, li) in lessons" :key="li" :id="'ls-' + li" class="lesson">
        <view class="lesson-title">
          <text class="lt-name">{{ ls.name }}</text>
          <text class="lt-count">{{ ls.chars.length }} 字</text>
        </view>
        <view class="grid">
          <view
            v-for="(c, ci) in ls.chars"
            :key="ci"
            class="card"
            :class="{ on: learnedMap[c.ch] }"
            :style="cellStyle"
            @tap="openAt(c.idx)"
          >
            <text class="big">{{ c.ch }}</text>
            <view class="pyrow">
              <zk-py :text="c.py" size="sm" />
              <view class="sound" @tap.stop="speak">
                <view class="sound-i"></view>
              </view>
            </view>
            <view v-if="c.words && c.words.length" class="words">
              <text v-for="(w, wi) in c.words" :key="wi" class="w">{{ w }}</text>
            </view>
          </view>
        </view>
      </view>
      <view class="tail">— {{ curBook.label }} 共 {{ curBook.charCount }} 字 —</view>
    </view>

    <!-- 详情弹层 -->
    <zk-detail
      :show="sheetShow"
      :item="cur"
      :meta="meta"
      :multi="curMulti"
      :learned="curLearned"
      :in-book="curInBook"
      :is-pad="isPad"
      :can-prev="curIdx > 0"
      :can-next="curIdx < flat.length - 1"
      @close="close"
      @prev="prev"
      @next="next"
      @learned="onLearned"
      @wordbook="onWordbook"
      @speak="speak"
    />
  </view>
</template>

<script>
import { loadIndex, loadBook, loadDict, loadMulti, loadDefs, splitLabel } from '@/common/data.js'
import * as store from '@/common/store.js'
import zkPy from '@/components/zk-py/zk-py.vue'
import zkDetail from '@/components/zk-detail/zk-detail.vue'

const LAST_BOOK_KEY = 'zk_last_book'

export default {
  components: { zkPy, zkDetail },
  data() {
    return {
      books: [],
      bookId: '',
      curBook: null,
      lessons: [],
      flat: [],
      loading: true,
      errorMsg: '',
      learnedMap: {},
      learnedCount: 0,
      sheetShow: false,
      curIdx: -1,
      cur: { ch: '', py: '', words: [], lesson: '', defs: [] },
      meta: {},
      curMulti: [],
      curLearned: false,
      curInBook: false,
      dict: null,
      multiMap: null,
      defsMap: null,
      isPad: false,
      vw: 0
    }
  },
  computed: {
    bookLabels() {
      return this.books.map((b) => '统编版语文' + b.label)
    },
    bookIndex() {
      const i = this.books.findIndex((b) => b.id === this.bookId)
      return i < 0 ? 0 : i
    },
    jumpLabels() {
      return this.lessons.map((l) => l.name)
    },
    // 列宽直接内联：小程序 wxss 的媒体查询在某些机型/端上不生效，
    // 内联样式优先级最高，列数由 JS 判宽决定，两端一致。
    // 列数（2026-10-24 用户定案，推翻早期"两端 4 列"）：手机 3 列（4 列太挤）；
    // 平板按视口宽度自适应，目标单格 ≥148px（原版 Web minmax(148px,1fr)），
    // 实算 600→3 列 / 768→4 列 / 900→5 列 / 1024+→6 列封顶。
    cellStyle() {
      const gap = this.isPad ? 14 : 8
      let cols = 3
      if (this.isPad) {
        const inner = this.vw - 48          // .lessons 平板左右各 24px
        cols = Math.floor((inner + gap) / (148 + gap))
        cols = Math.max(3, Math.min(cols, 6))
      }
      return { width: 'calc(' + (100 / cols).toFixed(3) + '% - ' + gap + 'px)' }
    }
  },
  onLoad() {
    this.measure()
    // #ifdef MP-WEIXIN
    if (typeof wx !== 'undefined' && wx.onWindowResize) {
      this._onResize = () => this.measure()
      wx.onWindowResize(this._onResize)
    }
    // #endif
    this.init()
  },
  onUnload() {
    // #ifdef MP-WEIXIN
    if (this._onResize && wx.offWindowResize) wx.offWindowResize(this._onResize)
    // #endif
  },
  onReady() {
    // 首屏布局完成后复测一次宽度，避免拿到初始视口
    this.measure()
  },
  onShow() {
    if (this.flat.length) this.refreshLearned()
  },
  methods: {
    measure() {
      let w = 375
      // #ifdef H5
      w = (typeof window !== 'undefined' && window.innerWidth) || 375
      // #endif
      // #ifndef H5
      try {
        w = uni.getSystemInfoSync().windowWidth || 375
      } catch (e) {}
      // #endif
      this.vw = w
      this.isPad = w >= 600
    },

    async init() {
      try {
        const idx = await loadIndex()
        this.books = (idx.books || []).map((b) => {
          const s = splitLabel(b.label)
          return { ...b, grade: s.grade, vol: s.vol }
        })
        let last = ''
        try {
          last = uni.getStorageSync(LAST_BOOK_KEY) || ''
        } catch (e) {}
        const first = this.books.find((b) => b.id === last) || this.books[0]
        if (!first) {
          this.errorMsg = '册目录为空'
          this.loading = false
          return
        }
        await this.pickBook(first.id)
      } catch (e) {
        this.errorMsg = '数据读取失败：' + (e && e.message ? e.message : e)
        this.loading = false
      }
    },

    async pickBook(id) {
      if (!id) return
      this.loading = true
      this.errorMsg = ''
      this.bookId = id
      this.curBook = this.books.find((b) => b.id === id) || null
      try {
        const bk = await loadBook(id)
        const flat = []
        const lessons = (bk.lessons || []).map((ls) => {
          const name = ls[0]
          const chars = (ls[1] || []).map((c) => {
            const item = {
              ch: c[0],
              py: c[1],
              words: c[2] || [],
              lesson: name,
              idx: flat.length
            }
            flat.push(item)
            return item
          })
          return { name, chars }
        })
        this.flat = flat
        this.lessons = lessons
        this.sheetShow = false
        this.curIdx = -1
        this.loading = false
        try {
          uni.setStorageSync(LAST_BOOK_KEY, id)
        } catch (e) {}
        this.refreshLearned()
        uni.pageScrollTo({ scrollTop: 0, duration: 0 })
      } catch (e) {
        this.errorMsg = '本册读取失败：' + (e && e.message ? e.message : e)
        this.loading = false
      }
    },

    onBookPick(e) {
      const b = this.books[Number(e.detail.value)]
      if (b) this.pickBook(b.id)
    },

    // 跳课：拿目标分组的实际位置再滚，不靠估算高度
    onJumpPick(e) {
      const li = Number(e.detail.value)
      if (isNaN(li)) return
      const q = uni.createSelectorQuery().in(this)
      q.select('#ls-' + li)
        .boundingClientRect()
        .selectViewport()
        .scrollOffset()
        .exec((res) => {
          const rect = res && res[0]
          const off = res && res[1]
          if (!rect || !off) return
          uni.pageScrollTo({ scrollTop: rect.top + off.scrollTop - 6, duration: 220 })
        })
    },

    refreshLearned() {
      const map = {}
      let n = 0
      this.flat.forEach((c) => {
        if (store.isLearned(c.ch)) {
          map[c.ch] = true
          n++
        }
      })
      this.learnedMap = map
      this.learnedCount = n
      if (this.curIdx >= 0) this.syncCurState()
    },

    async ensureDict() {
      if (this.dict) return this.dict
      try {
        this.dict = await loadDict()
      } catch (e) {
        this.dict = { radicals: {}, explanations: {}, multi: {} }
      }
      return this.dict
    },

    /** 多音字表：独立文件，按需加载一次 */
    async ensureMulti() {
      if (this.multiMap) return this.multiMap
      try {
        const d = await loadMulti()
        this.multiMap = (d && d.chars) || {}
      } catch (e) {
        this.multiMap = {}
      }
      return this.multiMap
    },

    /** 释义表：独立文件，按需加载一次（P2.5 重采，已清洗） */
    async ensureDefs() {
      if (this.defsMap) return this.defsMap
      try {
        const d = await loadDefs()
        this.defsMap = (d && d.chars) || {}
      } catch (e) {
        this.defsMap = {}
      }
      return this.defsMap
    },

    /** 把 [[册,课],...] 拼成「二年级上册 · 课文1」 */
    multiReadings(ch) {
      const rows = this.multiMap && this.multiMap[ch]
      if (!rows || !rows.length) return []
      return rows.map((r) => {
        const ls = r.lessons || []
        const from = ls.length
          ? ls.slice(0, 2).map((x) => x[0][0] + x[0].slice(3, 4) + ' · ' + x[1]).join('；')
          : ''
        return { py: r.py, isLesson: !!r.isLesson, words: r.words || [], from }
      })
    },

    async openAt(idx) {
      const c = this.flat[idx]
      if (!c) return
      this.curIdx = idx
      this.cur = { ...c, defs: [] }
      this.meta = {}
      this.curLearned = store.isLearned(c.ch)
      this.curInBook = store.inWordbook(c.ch)
      this.sheetShow = true

      const d = await this.ensureDict()
      await this.ensureMulti()
      const defs = await this.ensureDefs()
      // 字典异步加载期间可能已翻到别的字，只认当前这个
      if (this.cur.ch !== c.ch) return
      this.meta = (d.radicals && d.radicals[c.ch]) || {}
      const row = defs[c.ch]
      this.curMulti = this.multiReadings(c.ch)
      this.cur = { ...this.cur, defs: (row && row.defs) || [] }
    },

    syncCurState() {
      if (!this.cur || !this.cur.ch) return
      this.curLearned = store.isLearned(this.cur.ch)
      this.curInBook = store.inWordbook(this.cur.ch)
    },

    close() {
      this.sheetShow = false
    },

    prev() {
      if (this.curIdx > 0) this.openAt(this.curIdx - 1)
    },

    next() {
      if (this.curIdx < this.flat.length - 1) this.openAt(this.curIdx + 1)
    },

    onLearned() {
      if (this.curLearned) {
        uni.showToast({ title: '这个字已经学会啦', icon: 'none' })
        return
      }
      store.markLearned(this.cur.ch)
      this.curLearned = true
      this.refreshLearned()
      uni.showToast({ title: '+1★ 记下了', icon: 'none' })
    },

    onWordbook() {
      const on = store.toggleWordbook(this.cur.ch)
      this.curInBook = on
      uni.showToast({ title: on ? '已加入生字本' : '已移出生字本', icon: 'none' })
    },

    speak() {
      // P3 接 Edge TTS，先明确告知进度，不做假按钮
      uni.showToast({ title: '发音在 P3 阶段接入', icon: 'none' })
    }
  }
}
</script>

<style>
/* ============================================================
   视觉基线：public/index.html v3.52 的「纸卷」体系（DESIGN.md v2.00）
   米黄纸底 #F6F1E5 / 纸白卡 #FFFDF7 / 朱砂 #C93A2B / 金 #C9973F
   暖棕描边 #E6DDC8、暖棕投影，纸感全靠这两样，不要换成中性灰
   ============================================================ */
.page {
  min-height: 100vh;
  padding: 0 0 28px;
  box-sizing: border-box;
  background: #f6f1e5;
  background-image: radial-gradient(circle at 10% 12%, rgba(233, 190, 80, 0.1), rgba(233, 190, 80, 0) 42%),
    radial-gradient(circle at 92% 85%, rgba(201, 58, 43, 0.07), rgba(201, 58, 43, 0) 42%);
}

/* ---------- 品牌区 ---------- */
.brand {
  display: flex;
  align-items: center;
  padding: 12px 14px 8px;
}
.seal {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #d84937, #a3281c);
  box-shadow: 0 4px 10px rgba(163, 40, 28, 0.28);
}
.seal-t {
  color: #ffffff;
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-weight: 700;
  font-size: 22px;
  line-height: 22px;
}
.brand-txt {
  flex: 1;
  min-width: 0;
  margin-left: 11px;
  display: flex;
  flex-direction: column;
}
.brand-h1 {
  font-family: 'Noto Serif SC', 'Songti SC', 'STSong', 'SimSun', serif;
  font-size: 17px;
  font-weight: 900;
  letter-spacing: 0.5px;
  color: #33322e;
}
.brand-sub {
  display: none;
}
.stat {
  display: flex;
  align-items: baseline;
  flex: none;
  padding-left: 8px;
}
.stat-s {
  font-size: 11px;
  color: #c9973f;
  margin-right: 2px;
}
.stat-n {
  font-size: 15px;
  font-weight: 700;
  color: #a87c2c;
}
.stat-t {
  font-size: 11px;
  color: #a9a296;
  margin-left: 1px;
}

/* ---------- 控制区 ---------- */
.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  padding: 0 14px 8px;
}
.sel {
  display: flex;
  align-items: center;
  margin-right: 8px;
  margin-bottom: 6px;
  padding: 6px 13px;
  border: 1.5px solid #e6ddc8;
  border-radius: 999px;
  background: #fffdf7;
}
.sel-t {
  font-size: 13.5px;
  color: #33322e;
}
.sel-jump .sel-t {
  color: #6b675c;
}
.sel-caret {
  font-size: 9px;
  line-height: 9px;
  color: #a9a296;
  margin-left: 6px;
}

.tip {
  padding: 0 14px 4px;
  font-size: 11.5px;
  line-height: 1.65;
  color: #6b675c;
}
.tip-b {
  color: #a3281c;
  font-weight: 700;
  margin: 0 1px;
}

/* ---------- 课文分组 ---------- */
.lessons {
  padding: 6px 12px 0;
}
.lesson-title {
  display: flex;
  align-items: center;
  margin: 14px 0 10px;
  padding: 8px 12px;
  border-left: 4px solid #c9973f;
  border-radius: 0 10px 10px 0;
  background: linear-gradient(90deg, #f7ecd6, rgba(247, 236, 214, 0));
}
.lt-name {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #a3281c;
}
.lt-count {
  flex: none;
  font-size: 11px;
  color: #6b675c;
  background: #ffffff;
  border: 1px solid #f0dfbc;
  border-radius: 999px;
  padding: 1px 9px;
}

/* ---------- 字卡 ---------- */
.grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -4px;
}
.card {
  position: relative;
  box-sizing: border-box;
  margin: 0 4px 8px;
  padding: 14px 4px 12px;
  min-height: 152px;
  border: 1.5px solid #e6ddc8;
  border-radius: 12px;
  background: #fffdf7;
  box-shadow: 0 2px 6px rgba(90, 70, 30, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.card:active {
  transform: translateY(-2px);
  border-color: #d8c9a6;
  box-shadow: 0 6px 18px rgba(90, 70, 30, 0.14);
}
.big {
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 44px;
  line-height: 54px;
  font-weight: 700;
  color: #33322e;
}
.pyrow {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 5px;
}
.sound {
  flex: none;
  width: 20px;
  height: 20px;
  margin-left: 4px;
  border-radius: 50%;
  border: 1.5px solid #c9973f;
  background: #f7ecd6;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sound:active {
  background: #c9973f;
}
.sound-i {
  width: 11px;
  height: 11px;
  background-repeat: no-repeat;
  background-size: 100% 100%;
  background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHZpZXdCb3g9JzAgMCAyNCAyNCcgZmlsbD0nbm9uZScgc3Ryb2tlPScjOEE2NDIwJyBzdHJva2Utd2lkdGg9JzIuMicgc3Ryb2tlLWxpbmVjYXA9J3JvdW5kJyBzdHJva2UtbGluZWpvaW49J3JvdW5kJz48cGF0aCBkPSdNMTEgNSA2IDlIM3Y2aDNsNSA0VjV6Jy8+PHBhdGggZD0nTTE1LjUgOC41YTUgNSAwIDAgMSAwIDcnLz48cGF0aCBkPSdNMTguNSA1LjVhOSA5IDAgMCAxIDAgMTMnLz48L3N2Zz4=");
}
.words {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 8px;
}
.w {
  font-size: 10px;
  line-height: 14px;
  color: #7a7465;
  background: #f7ecd6;
  border: 1px solid #f0dfbc;
  border-radius: 999px;
  padding: 1px 4px;
  margin: 2px 1px 0;
}
/* 已学：右上角绿点（原版无此标记，属小程序新增的激励反馈） */
.card.on::after {
  content: '';
  position: absolute;
  top: 6px;
  right: 7px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #5d8a66;
}

.tail {
  padding: 16px 0 4px;
  text-align: center;
  font-size: 11px;
  color: #bdb5a4;
}
.hint {
  padding: 60px 0;
  text-align: center;
  font-size: 13px;
  color: #8a8378;
}

/* ============================================================
   平板（≥600px）：6 列 + 原版桌面尺寸
   不用 media query —— 小程序 wxss 的媒体查询在部分机型上不生效，
   统一由 JS 判宽后挂 .pad，两端行为一致（DESIGN.md 9.6）
   ============================================================ */
.page.pad .brand {
  padding: 16px 24px 10px;
}
.page.pad .seal {
  width: 46px;
  height: 46px;
  border-radius: 12px;
}
.page.pad .seal-t {
  font-size: 26px;
  line-height: 26px;
}
.page.pad .brand-txt {
  margin-left: 12px;
}
.page.pad .brand-h1 {
  font-size: 20px;
}
.page.pad .brand-sub {
  display: block;
  font-size: 12px;
  color: #6b675c;
  margin-top: 1px;
}
.page.pad .controls {
  padding: 0 24px 8px;
}
.page.pad .sel {
  padding: 7px 14px;
}
.page.pad .sel-t {
  font-size: 14px;
}
.page.pad .tip {
  padding: 0 24px 4px;
  font-size: 12px;
}
.page.pad .lessons {
  padding: 10px 24px 0;
}
.page.pad .lesson-title {
  margin: 20px 0 12px;
  padding: 9px 14px;
}
.page.pad .lt-name {
  font-size: 14.5px;
}
.page.pad .grid {
  margin: 0 -7px;
}
.page.pad .card {
  margin: 0 7px 14px;
  padding: 24px 12px 18px;
  min-height: 206px;
  border-radius: 14px;
}
.page.pad .big {
  font-size: 72px;
  line-height: 84px;
}
.page.pad .sound {
  width: 24px;
  height: 24px;
}
.page.pad .sound-i {
  width: 13px;
  height: 13px;
}
.page.pad .w {
  font-size: 11.5px;
  line-height: 16px;
  padding: 1px 8px;
  margin: 2px 2px 0;
}
</style>
