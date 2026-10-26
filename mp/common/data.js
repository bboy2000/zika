/**
 * 数据层 —— 编译期静态 import + 内存直读
 *
 * v0.3.1 起改为静态 import：微信打包后 FileSystemManager 无法可靠读取代码包内
 * JSON（报 permission denied / no such file），编译期注入是唯一稳妥方式。
 * 数据文件在 common/data-json/（不在 static/，避免打包双份体积）。
 * 代价：数据随主包常驻（约 1.4MB，主包限额 2MB 内）；换取零运行时读取延迟。
 *
 * 数据再生成工具（build-data.py / build-multi.py / build-defs.py /
 * publish-audio-map.py）已同步改写到 mp/common/data-json/。
 */

import indexData from './data-json/index.json'
import dictData from './data-json/dict.json'
import multiData from './data-json/multi_v2.json'
import defsData from './data-json/defs_v2.json'
import audioMapData from './data-json/audio_map.json'

import yiShang from './data-json/books/yi_shang.json'
import yiXia from './data-json/books/yi_xia.json'
import erShang from './data-json/books/er_shang.json'
import erXia from './data-json/books/er_xia.json'
import sanShang from './data-json/books/san_shang.json'
import sanXia from './data-json/books/san_xia.json'
import siShang from './data-json/books/si_shang.json'
import siXia from './data-json/books/si_xia.json'
import wuShang from './data-json/books/wu_shang.json'
import wuXia from './data-json/books/wu_xia.json'
import liuShang from './data-json/books/liu_shang.json'
import liuXia from './data-json/books/liu_xia.json'

const BOOKS = {
  yi_shang: yiShang, yi_xia: yiXia,
  er_shang: erShang, er_xia: erXia,
  san_shang: sanShang, san_xia: sanXia,
  si_shang: siShang, si_xia: siXia,
  wu_shang: wuShang, wu_xia: wuXia,
  liu_shang: liuShang, liu_xia: liuXia
}

const DATA = {
  'index.json': indexData,
  'dict.json': dictData,
  'multi_v2.json': multiData,
  'defs_v2.json': defsData,
  'audio_map.json': audioMapData
}

const cache = Object.create(null)

function resolve(rel) {
  // rel 形如 'data-json/index.json' / 'data-json/books/er_shang.json'
  const name = rel.replace(/^data-json\//, '')
  if (DATA[name]) return DATA[name]
  const m = name.match(/^books\/([\w-]+)\.json$/)
  if (m && BOOKS[m[1]]) return BOOKS[m[1]]
  throw new Error('未知数据文件: ' + rel)
}

/** 兼容旧接口：现在数据已在内存，直接返回 */
export function loadJSON(rel) {
  if (!cache[rel]) {
    try {
      cache[rel] = Promise.resolve(resolve(rel))
    } catch (e) {
      return Promise.reject(e)
    }
  }
  return cache[rel]
}

/** 册目录：{version, books:[{id,label,lessonCount,charCount,size}]} */
export const loadIndex = () => loadJSON('data-json/index.json')

/** 单册写字表：{id,label,lessons:[[课名,[[字,拼音,[词...]],...]],...],count} */
export const loadBook = (id) => loadJSON('data-json/books/' + id + '.json')

/** 字库：{radicals,explanations,multi} */
export const loadDict = () => loadJSON('data-json/dict.json')

/**
 * 多音字表（P2 重建，tools/build-multi.py 产出）
 * { _meta:{version,count}, chars:{ 字: [{py,tone3,isLesson,support,lessons,words}] } }
 */
export const loadMulti = () => loadJSON('data-json/multi_v2.json')

/** 册 id → {grade:'一年级', vol:'上册'} */
export function splitLabel(label) {
  const g = label.slice(0, 3)
  const v = label.slice(3)
  return { grade: g, vol: v }
}

/**
 * 释义表（P2.5 重采，tools/build-defs.py 产出）
 * { version, chars:{ 字: {py, defs:[义项...], src} } }
 */
export const loadDefs = () => loadJSON('data-json/defs_v2.json')
