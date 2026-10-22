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

/**
 * 多音字表（P2 重建，tools/build-multi.py 产出）
 * { _meta:{version,count}, chars:{ 字: [{py,tone3,isLesson,support,lessons,words}] } }
 * 与主数据分离：主库每字只标本课读音，这里补全该字的其他常用读音。
 */
export const loadMulti = () => loadJSON('static/data/multi_v2.json')

/** 册 id → {grade:'一年级', vol:'上册'} */
export function splitLabel(label) {
  const g = label.slice(0, 3)
  const v = label.slice(3)
  return { grade: g, vol: v }
}

/**
 * 释义表（P2.5 重采，tools/build-defs.py 产出）
 * { version, chars:{ 字: {py, defs:[义项...], src} } }
 *
 * 为什么新开一张表而不复用 dict.json 的 explanations：
 * 旧库是古汉语字典抓取残留（111 字缺失、328 条含〈古〉〈引〉标记、307 条引号错位），
 * 清洗规则补不回来——只能重采。新表按「本课读音」取义项，与多音字表口径一致。
 */
export const loadDefs = () => loadJSON('static/data/defs_v2.json')
