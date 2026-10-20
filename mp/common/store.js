/**
 * 本地学习状态（P1 先用 storage，P6 换成云数据库 + 软删除同步）
 * 结构：{ learned: { 字: 时间戳 }, wordbook: { 字: 时间戳 } }
 * 用对象而不是数组，查已学是 O(1)，列表页每个字都要查
 */

const KEY = 'zk_local_v1'

function read() {
  try {
    const d = uni.getStorageSync(KEY)
    if (d && typeof d === 'object') return { learned: d.learned || {}, wordbook: d.wordbook || {} }
  } catch (e) {}
  return { learned: {}, wordbook: {} }
}

function write(d) {
  try {
    uni.setStorageSync(KEY, d)
  } catch (e) {}
}

export function isLearned(ch) {
  return !!read().learned[ch]
}

export function markLearned(ch) {
  const d = read()
  d.learned[ch] = Date.now()
  write(d)
}

export function inWordbook(ch) {
  return !!read().wordbook[ch]
}

export function toggleWordbook(ch) {
  const d = read()
  if (d.wordbook[ch]) delete d.wordbook[ch]
  else d.wordbook[ch] = Date.now()
  write(d)
  return !!d.wordbook[ch]
}

export function stats() {
  const d = read()
  return { learned: Object.keys(d.learned).length, wordbook: Object.keys(d.wordbook).length }
}
