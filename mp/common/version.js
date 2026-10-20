/**
 * 全局版本号：每次改动递增（P0 = v0.1.0，v0.1.1 = 数据层+双端配置）
 * 规则：改动提交信息与本文件版本号必须一致
 */
export const APP_VERSION = 'v0.1.2'

/**
 * 设计令牌 —— 与 DESIGN.md v1.00 一一对应
 * 页面里禁止硬编码色值，一律引用这里或 uni.scss 的 CSS 变量
 */
export const THEME = {
  // 朱砂（主色）
  primary: '#D94F3D',
  primaryDeep: '#B53A2B',
  primaryLight: '#FBE7E3',
  primaryWash: '#FDF3F0',

  // 奖励金（只用于激励元素）
  gold: '#F2B230',
  goldDeep: '#D9941C',
  goldLight: '#FEF4DE',

  // 纸与墨
  bg: '#FDF9F3',
  card: '#FFFFFF',
  text: '#2B2B2B',
  text2: '#5C574F',
  sub: '#8A8378',
  line: '#EDE6DA',
  lineSoft: '#F5EFE5',

  // 语义（答错用 warn，不用红）
  success: '#57A88F',
  successLight: '#E8F4F0',
  warn: '#E8A33D',
  warnLight: '#FDF2E0'
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

/** 激励等级阶梯（累计字数达标晋级） */
export const LEVELS = [
  { lv: 1, need: 0,    name: '蒙童',   color: '#8A8378' },
  { lv: 2, need: 50,   name: '学童',   color: '#57A88F' },
  { lv: 3, need: 200,  name: '小秀才', color: '#5B8FA8' },
  { lv: 4, need: 500,  name: '小举人', color: '#D9941C' },
  { lv: 5, need: 1000, name: '小进士', color: '#D94F3D' },
  { lv: 6, need: 2000, name: '小状元', color: '#B53A2B' }
]
