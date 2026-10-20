<template>
  <view class="page" :class="{ pad: isPad }">
    <!-- 顶栏：册次 + 已学进度（激励可见化） -->
    <view class="topbar">
      <view class="tb-l">
        <text class="tb-title">写字表</text>
        <text class="tb-sub">{{ curBook ? curBook.label : '加载中' }}</text>
      </view>
      <view class="tb-r">
        <text class="tb-star">★</text>
        <text class="tb-num">{{ learnedCount }}</text>
        <text class="tb-total">/ {{ curBook ? curBook.charCount : 0 }}</text>
      </view>
    </view>

    <!-- 册次选择：12 册横滑 -->
    <scroll-view class="books" scroll-x :show-scrollbar="false" :scroll-into-view="scrollTo">
      <view
        v-for="b in books"
        :key="b.id"
        :id="'bk-' + b.id"
        class="chip"
        :class="{ on: b.id === bookId }"
        @tap="pickBook(b.id)"
      >
        <text class="chip-g">{{ b.grade }}</text>
        <text class="chip-v">{{ b.vol }}</text>
      </view>
    </scroll-view>

    <!-- 列表 -->
    <view v-if="loading" class="tip">正在打开课本…</view>
    <view v-else-if="errorMsg" class="tip">{{ errorMsg }}</view>
    <view v-else class="lessons">
      <view v-for="(ls, li) in lessons" :key="li" class="lesson">
        <view class="ls-head">
          <view class="ls-bar"></view>
          <text class="ls-name">{{ ls.name }}</text>
          <text class="ls-count">{{ ls.chars.length }} 字</text>
        </view>
        <view class="grid">
          <view
            v-for="(c, ci) in ls.chars"
            :key="ci"
            class="cell"
            :class="{ learned: learnedMap[c.ch] }"
            :style="cellStyle"
            @tap="openAt(c.idx)"
          >
            <text class="zi">{{ c.ch }}</text>
            <view class="py-wrap">
              <zk-py :text="c.py" size="sm" />
            </view>
            <view class="spk" @tap.stop="speak">
              <text class="spk-i">♪</text>
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
import { loadIndex, loadBook, loadDict, splitLabel, cleanExplanation } from '@/common/data.js'
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
      scrollTo: '',
      learnedMap: {},
      learnedCount: 0,
      sheetShow: false,
      curIdx: -1,
      cur: { ch: '', py: '', words: [], lesson: '', exp: '' },
      meta: {},
      curLearned: false,
      curInBook: false,
      dict: null,
      isPad: false,
      vw: 0
    }
  },
  computed: {
    // 列宽直接内联：小程序 wxss 的媒体查询在某些机型/端上不生效，
    // 内联样式优先级最高，手机 4 列 / 平板 6 列由 JS 判宽决定，两端一致
    cellStyle() {
      return { width: this.isPad ? 'calc(16.6667% - 8px)' : 'calc(25% - 8px)' }
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
      this.scrollTo = 'bk-' + id
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

    async openAt(idx) {
      const c = this.flat[idx]
      if (!c) return
      this.curIdx = idx
      this.cur = { ...c, exp: '' }
      this.meta = {}
      this.curLearned = store.isLearned(c.ch)
      this.curInBook = store.inWordbook(c.ch)
      this.sheetShow = true

      const d = await this.ensureDict()
      // 字典异步加载期间可能已翻到别的字，只认当前这个
      if (this.cur.ch !== c.ch) return
      this.meta = (d.radicals && d.radicals[c.ch]) || {}
      const exp = cleanExplanation(d.explanations && d.explanations[c.ch])
      this.cur = { ...this.cur, exp }
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
.page {
  min-height: 100vh;
  padding: 0 0 24px;
  box-sizing: border-box;
}

/* ---------- 顶栏 ---------- */
.topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 12px 16px 6px;
}
.tb-l {
  display: flex;
  align-items: baseline;
}
.tb-title {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #2b2b2b;
}
.tb-sub {
  margin-left: 8px;
  font-size: 12px;
  color: #8a8378;
}
.tb-r {
  display: flex;
  align-items: baseline;
}
.tb-star {
  font-size: 12px;
  color: #f2b230;
  margin-right: 3px;
}
.tb-num {
  font-size: 15px;
  font-weight: 700;
  color: #d9941c;
}
.tb-total {
  font-size: 11px;
  color: #a9a296;
  margin-left: 2px;
}

/* ---------- 册次条 ---------- */
.books {
  white-space: nowrap;
  padding: 6px 12px 10px;
  box-sizing: border-box;
}
.chip {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 52px;
  margin-right: 8px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 12px;
  box-sizing: border-box;
  vertical-align: top;
}
.chip-g {
  font-size: 10px;
  line-height: 13px;
  color: #a9a296;
}
.chip-v {
  font-size: 14px;
  line-height: 18px;
  font-weight: 600;
  color: #5c574f;
}
.chip.on {
  background: #ffffff;
  border-color: #d94f3d;
  box-shadow: 0 2px 8px rgba(43, 43, 43, 0.06);
}
.chip.on .chip-g {
  color: #d94f3d;
  opacity: 0.75;
}
.chip.on .chip-v {
  color: #d94f3d;
}

/* ---------- 课文分组 ---------- */
.lessons {
  padding: 0 16px;
}
.ls-head {
  display: flex;
  align-items: center;
  margin: 16px 0 8px;
}
.ls-bar {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #d94f3d;
  margin-right: 7px;
}
.ls-name {
  font-size: 14px;
  font-weight: 600;
  color: #2b2b2b;
}
.ls-count {
  margin-left: 7px;
  font-size: 11px;
  color: #a9a296;
}

.grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -4px;
}
.cell {
  position: relative;
  width: calc(25% - 8px);
  margin: 0 4px 8px;
  padding: 10px 2px 7px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #ffffff;
  border: 1px solid #f5efe5;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(43, 43, 43, 0.04);
}
.cell:active {
  transform: scale(0.97);
}
.zi {
  font-family: 'zika-kai', 'Kaiti SC', 'STKaiti', 'KaiTi', '楷体', serif;
  font-size: 46px;
  line-height: 50px;
  font-weight: 400;
  color: #2b2b2b;
}
.py-wrap {
  margin-top: 4px;
  max-width: 100%;
  display: flex;
  justify-content: center;
}
.spk {
  margin-top: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fdf3f0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.spk-i {
  font-size: 12px;
  line-height: 12px;
  color: #c9756a;
}
.cell.learned::after {
  content: '';
  position: absolute;
  top: 7px;
  right: 7px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #57a88f;
}

.tail {
  padding: 18px 0 6px;
  text-align: center;
  font-size: 11px;
  color: #c1bab0;
}
.tip {
  padding: 60px 0;
  text-align: center;
  font-size: 13px;
  color: #a9a296;
}

/* 平板：6 列 + 更大留白
   不用 media query：小程序 wxss 的媒体查询在部分机型上不生效，
   统一由 JS（getSystemInfo）判宽后挂 .pad，两端行为一致 */
.page.pad .topbar {
  padding: 16px 24px 8px;
}
.page.pad .books {
  padding: 8px 20px 12px;
}
.page.pad .lessons {
  padding: 0 24px;
}
.page.pad .ls-head {
  margin: 20px 0 10px;
}
</style>
