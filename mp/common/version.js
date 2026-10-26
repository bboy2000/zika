/**
 * 全局版本号：每次改动递增（P0 = v0.1.0）
 * 规则：改动提交信息与本文件版本号必须一致
 */
export const APP_VERSION = 'v0.3.2'

/**
 * 设计令牌 —— 与 DESIGN.md v2.03 一一对应
 * v2.00 起视觉基线回到 Web 版 v3.52 的「纸卷」体系（米黄纸底 + 纸白卡 + 朱砂 + 金）
 * 页面里禁止硬编码色值，一律引用 uni.scss 或这里的令牌
 */
export const THEME = {
  // 朱砂（主色）
  primary: '#C93A2B',
  primaryDeep: '#A3281C',
  primaryLight: '#F9E9E4',
  primaryWash: '#FCF2EE',

  // 奖励金（激励元素 + 组词徽章）
  gold: '#C9973F',
  goldDeep: '#A87C2C',
  goldLight: '#F7ECD6',
  goldLine: '#F0DFBC',

  // 纸与墨
  bg: '#F6F1E5',
  card: '#FFFDF7',
  text: '#33322E',
  text2: '#6B675C',
  sub: '#8A8378',
  line: '#E6DDC8',
  lineSoft: '#F0E9D8',

  // 格线
  grid: '#D9C69A',
  gridDiag: '#EFE4C4',
  pyLine: '#B8C8DC',
  pyInk: '#2B2F36',

  // 语义（答错用 warn，不用红）
  success: '#5D8A66',
  successLight: '#E7F0E6',
  warn: '#C9973F',
  warnLight: '#F7ECD6'
}

/** 间距基数 4px */
export const SPACE = { s1: 4, s2: 8, s3: 12, s4: 16, s5: 24, s6: 32, s7: 48 }

/** 动效 */
export const MOTION = {
  ease: 'cubic-bezier(.34,1.56,.64,1)',
  fast: 160,
  base: 260,
  reward: 720
}

/**
 * 详情弹窗（DESIGN.md 5.5）—— 两端都是居中弹窗
 * 贴底会被原生 tabBar 压住底栏按钮，居中四周留 16px 天然躲开
 */
export const SHEET = {
  mask: 'rgba(46,38,24,.45)',
  phone: { maxWidth: '100%', radius: 16, maxHeight: '86%', tz: 180, big: 60 },
  pad: { maxWidth: 520, radius: 20, maxHeight: '86%', tz: 250, big: 72 }
}

/** 列数：手机 3 列（2026-10-24 定案，4 列太挤）；平板按视口自适应 3~6 列，目标格宽 ≥148px */
/** 多音字（P2）：单字最多展示几个读音 / 每读音最多几个组词 */
export const MULTI = {
  maxReadings: 3,
  wordsPerReading: 3
}

export const GRID_COLS = { phone: 3, pad: 'auto', padMinCell: 148, padMax: 6 }

/** 激励等级阶梯（累计字数达标晋级） */
export const LEVELS = [
  { lv: 1, need: 0,    name: '蒙童',   color: '#8A8378' },
  { lv: 2, need: 50,   name: '学童',   color: '#5D8A66' },
  { lv: 3, need: 200,  name: '小秀才', color: '#5B8FA8' },
  { lv: 4, need: 500,  name: '小举人', color: '#A87C2C' },
  { lv: 5, need: 1000, name: '小进士', color: '#C93A2B' },
  { lv: 6, need: 2000, name: '小状元', color: '#A3281C' }
]
