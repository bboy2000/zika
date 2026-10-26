/**
 * 笔顺数据层（P4）：按字从云存储取 per-char JSON
 *
 * 数据格式（tools/build_perchar.py 产出，GF 0023-2020 校验）：
 *   n: ['横', '竖钩', ...]  逐笔名称
 *   s: ['M 518 382 Q ...']  逐笔 SVG 路径（1024 坐标系 y 向上，占格 y∈[0,900]）
 *   m: [[[x,y],...], ...]   逐笔中轴线
 *
 * fileID 运行时拼接（同 audio.js CLOUD_PREFIX 方案，包内零体积）：
 *   cloud://jiangbian-.../strokes/<字>.json
 *
 * 缓存：内存 → 本地 storage（FIFO 上限 400 字 ≈ 1MB，storage 总量 10MB 内）
 */
const CLOUD_PREFIX = 'cloud://jiangbian-d5gnaoxv1ae2d4e78.6a69-jiangbian-d5gnaoxv1ae2d4e78-1516998999/strokes/'
const IDX_KEY = 'sk_idx'
const IDX_MAX = 400

let cloudInited = false
function ensureCloud() {
  if (cloudInited) return
  // #ifdef MP-WEIXIN
  wx.cloud.init({ env: 'jiangbian-d5gnaoxv1ae2d4e78', traceUser: false })
  // #endif
  cloudInited = true
}

const mem = {}

function diskGet(ch) {
  try {
    const d = uni.getStorageSync('sk_' + ch)
    return d && d.n ? d : null
  } catch (e) {
    return null
  }
}

function diskSet(ch, d) {
  try {
    uni.setStorageSync('sk_' + ch, d)
    let idx = uni.getStorageSync(IDX_KEY) || []
    if (idx.indexOf(ch) < 0) idx.push(ch)
    while (idx.length > IDX_MAX) {
      const old = idx.shift()
      if (old !== ch) uni.removeStorageSync('sk_' + old)
    }
    uni.setStorageSync(IDX_KEY, idx)
  } catch (e) { /* storage 满不影响功能 */ }
}

/**
 * 取单字笔顺数据。失败 reject（调用方降级为静态字展示）。
 */
export function loadStrokes(ch) {
  if (!ch) return Promise.reject(new Error('empty char'))
  if (mem[ch]) return Promise.resolve(mem[ch])
  const cached = diskGet(ch)
  if (cached) {
    mem[ch] = cached
    return Promise.resolve(cached)
  }

  // #ifdef MP-WEIXIN
  ensureCloud()
  return new Promise((resolve, reject) => {
    wx.cloud.downloadFile({
      fileID: CLOUD_PREFIX + ch + '.json',
      success: (res) => {
        try {
          const d = JSON.parse(wx.getFileSystemManager().readFileSync(res.tempFilePath, 'utf8'))
          mem[ch] = d
          diskSet(ch, d)
          resolve(d)
        } catch (e) {
          reject(e)
        }
      },
      fail: reject
    })
  })
  // #endif

  // #ifndef MP-WEIXIN
  // H5 预览：数据目录由预览服务提供（无则失败走静态降级）
  return fetch('/strokes/' + encodeURIComponent(ch) + '.json')
    .then((r) => r.json())
    .then((d) => {
      mem[ch] = d
      return d
    })
  // #endif
}
