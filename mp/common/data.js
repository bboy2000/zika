/**
 * 数据层 —— 读代码包内 JSON + 内存缓存
 *
 * 为什么不 import：12 册 + 字典共 530KB，全部 import 会一次性进主包 js 并常驻内存。
 * 按需读包内文件，切册才加载该册（最大 12KB），字典首次进详情才加载。
 *
 * 小程序端用 FileSystemManager 读代码包文件（包内文件不走网络，无需 downloadFile）
 * H5 端（预览用）走 fetch
 */

const cache = Object.create(null)

function readRaw(rel) {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    const fs = wx.getFileSystemManager()
    let raw = null
    try {
      raw = fs.readFileSync(rel, 'utf8')
    } catch (e) {
      // 少数基础库要求带前导斜杠，兜底再试一次
      try {
        raw = fs.readFileSync('/' + rel, 'utf8')
      } catch (e2) {
        reject(e2)
        return
      }
    }
    try {
      resolve(JSON.parse(raw))
    } catch (e) {
      reject(e)
    }
    // #endif

    // #ifndef MP-WEIXIN
    fetch('/' + rel)
      .then((r) => r.json())
      .then(resolve)
      .catch(reject)
    // #endif
  })
}

export function loadJSON(rel) {
  if (cache[rel]) return Promise.resolve(cache[rel])
  return readRaw(rel).then((d) => {
    cache[rel] = d
    return d
  })
}

/** 册目录：{version, books:[{id,label,lessonCount,charCount,size}]} */
export const loadIndex = () => loadJSON('static/data/index.json')

/** 单册写字表：{id,label,lessons:[[课名,[[字,拼音,[词...]],...]],...],count} */
export const loadBook = (id) => loadJSON('static/data/books/' + id + '.json')

/** 字库：{radicals,explanations,multi} */
export const loadDict = () => loadJSON('static/data/dict.json')

/** 册 id → {grade:'一年级', vol:'上册'} */
export function splitLabel(label) {
  const g = label.slice(0, 3)
  const v = label.slice(3)
  return { grade: g, vol: v }
}

/**
 * 释义数据清洗（旧库是词典拼接，含 ∪ 『 等残留与截断拼音）
 * P2 会整体重采，这里先做闸门：不合格就返回空，宁可不显示也不给孩子看乱码
 */
export function cleanExplanation(s) {
  if (!s || typeof s !== 'string') return ''
  if (/[∪『』\[\]\ufffd]/.test(s)) return ''
  if (/^[a-zA-Zàáǎāèéěēìíǐīòóǒōùúǔūǖǘǚǜ]+\s*[；;]/.test(s)) return ''
  let t = s.replace(/；/g, '；').replace(/\s+/g, ' ').trim()
  // 只取第一条义项，旧数据多条拼接读起来很乱
  const first = t.split('；')[0]
  t = first.length > 40 ? first.slice(0, 40) + '…' : first
  return t
}
