/**
 * 播放层（P3）：InnerAudioContext 单例播放，按 key 查 audio_map
 *
 * key 规则（与 tools/synth-audio.py 一致）：
 *   单字读音  c:{字}:{tone3}   如 c:长:zhang3、c:干:gan1
 *   组词整词  w:{词}           如 w:一个（整词连贯，不逐字拼接）
 *
 * src 规则：
 *   小程序端  fileID（云存储）—— P3-3 开通云开发上传后由 publish 脚本回填
 *   H5 预览   /audio/{file}    —— 预览服务的 dist 里手动放 audio/ 目录（不进源码，避免包超限）
 *
 * 为什么不逐字拼：用户明确否决过「一个+个」式的逐字拼接发音，组词一律整词合成。
 */
import { loadJSON } from './data.js'

const TONEMAP = {
  'ā': ['a', 1], 'á': ['a', 2], 'ǎ': ['a', 3], 'à': ['a', 4],
  'ē': ['e', 1], 'é': ['e', 2], 'ě': ['e', 3], 'è': ['e', 4],
  'ī': ['i', 1], 'í': ['i', 2], 'ǐ': ['i', 3], 'ì': ['i', 4],
  'ō': ['o', 1], 'ó': ['o', 2], 'ǒ': ['o', 3], 'ò': ['o', 4],
  'ū': ['u', 1], 'ú': ['u', 2], 'ǔ': ['u', 3], 'ù': ['u', 4],
  'ǖ': ['v', 1], 'ǘ': ['v', 2], 'ǚ': ['v', 3], 'ǜ': ['v', 4],
  'ü': ['v', 0]
}

/** 带调拼音 -> 数字调 slug，与 multi_v2.json 的 tone3 同格式（cháng->chang2，轻声 le 无后缀） */
export function tone3(py) {
  const p = (py || '').trim().toLowerCase()
  const out = []
  let tone = ''
  for (const c of p) {
    const e = TONEMAP[c]
    if (e) {
      out.push(e[0])
      if (e[1]) tone = String(e[1])
    } else {
      out.push(c)
    }
  }
  return out.join('') + tone
}

let mapCache = null

export function loadAudioMap() {
  if (mapCache) return Promise.resolve(mapCache)
  return loadJSON('static/data/audio_map.json').then((m) => {
    mapCache = m
    return m
  })
}

let cur = null

export function stopSpeak() {
  if (cur) {
    try { cur.stop() } catch (e) { /* 已销毁则忽略 */ }
    cur = null
  }
}

/**
 * 播一条音频。返回 false 表示该 key 没有音频（调用方负责提示）。
 * 正在播的会被打断（连点下一个字立即换音，符合字卡交互直觉）。
 */
export async function speakAudio(key) {
  let m
  try {
    m = await loadAudioMap()
  } catch (e) {
    return false
  }
  const en = m && m.entries && m.entries[key]
  if (!en) return false

  let src = ''
  // #ifdef MP-WEIXIN
  src = en.fileID || ''
  // #endif
  // #ifndef MP-WEIXIN
  src = '/audio/' + en.file
  // #endif
  if (!src) return false

  stopSpeak()
  cur = uni.createInnerAudioContext()
  cur.src = src
  cur.play()
  return true
}

/** 便捷构造 key */
export function charKey(ch, py) {
  return 'c:' + ch + ':' + tone3(py)
}

export function wordKey(w) {
  return 'w:' + w
}
