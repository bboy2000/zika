#!/usr/bin/env node
/**
 * 音频上传云存储（P3-3）：audio_build/*.mp3 -> 微信云开发 云存储
 *
 * 前置条件（用户操作）：
 *   1. 微信小程序后台注册拿到真实 appid（当前 manifest.json 为空、dist 为 touristappid）
 *   2. 微信开发者工具打开 mp/dist 项目 -> 云开发 -> 开通 -> 记下环境 ID
 *   3. 云开发控制台「设置-全局设置-生成密钥」下载 JSON，把 secretId/secretKey 填到
 *      环境变量 TCB_SECRET_ID / TCB_SECRET_KEY，环境 ID 填 TCB_ENV_ID
 *
 * 行为：
 *   - 源：E:/字卡项目/audio_build 里 audio_map.json 引用的全部文件（单字 c_* + 组词 w_*）
 *   - 云端路径：audio/<原名>
 *   - 断点续传：已生成的 fileid_map.json 里有的条目跳过（--force 全量重传）
 *   - 产出：E:/字卡项目/audio_build/fileid_map.json  { key: fileID }
 *   - 之后跑 publish-audio-map.py 自动回填 fileID 进小程序 audio_map
 *
 * 用法：
 *   TCB_SECRET_ID=xxx TCB_SECRET_KEY=xxx TCB_ENV_ID=xxx node tools/upload-audio.js [--force]
 */
const fs = require('fs')
const path = require('path')
const CloudBase = require('@cloudbase/manager-node')

const ABDIR = path.join(__dirname, '..', '..', 'audio_build')
const MAP = path.join(ABDIR, 'audio_map.json')
const OUT = path.join(ABDIR, 'fileid_map.json')
const CONCURRENCY = 5

const { TCB_SECRET_ID, TCB_SECRET_KEY, TCB_ENV_ID } = process.env
if (!TCB_SECRET_ID || !TCB_SECRET_KEY || !TCB_ENV_ID) {
  console.error('缺少环境变量 TCB_SECRET_ID / TCB_SECRET_KEY / TCB_ENV_ID')
  process.exit(1)
}

const sleep = ms => new Promise(r => setTimeout(r, ms))

;(async () => {
  const map = JSON.parse(fs.readFileSync(MAP, 'utf8'))
  const entries = map.entries
  const keys = Object.keys(entries)
  console.log(`audio_map 共 ${keys.length} 条`)

  const fileids = fs.existsSync(OUT) && !process.argv.includes('--force')
    ? JSON.parse(fs.readFileSync(OUT, 'utf8'))
    : {}

  const todo = keys.filter(k => {
    const f = entries[k].file
    return fs.existsSync(path.join(ABDIR, f)) && !fileids[k]
  })
  const skipLocal = keys.length - todo.length - Object.keys(fileids).length
  console.log(`已有 fileID: ${Object.keys(fileids).length}  缺本地文件: ${skipLocal}  待传: ${todo.length}`)
  if (!todo.length) { console.log('无需上传'); return }

  const app = new CloudBase({ secretId: TCB_SECRET_ID, secretKey: TCB_SECRET_KEY, envId: TCB_ENV_ID })
  const storage = app.storage

  let ok = 0, fail = 0
  const save = () => fs.writeFileSync(OUT, JSON.stringify(fileids, null, 1))

  async function worker(queue) {
    while (queue.length) {
      const k = queue.shift()
      const f = entries[k].file
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          const r = await storage.uploadFile({
            localPath: path.join(ABDIR, f),
            cloudPath: 'audio/' + f,
          })
          fileids[k] = r.fileID
          ok++
          if (ok % 50 === 0) { save(); console.log(`进度 ${ok}/${todo.length} (失败${fail})`) }
          break
        } catch (e) {
          const msg = String(e.message || e)
          if (attempt === 3) { fail++; console.error(`FAIL ${k}: ${msg.slice(0, 120)}`) }
          else await sleep(2000 * attempt)
        }
      }
      await sleep(80) // 轻微限速，防限流
    }
  }

  const queue = todo.slice()
  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker(queue)))
  save()
  console.log(`完成：成功 ${ok} 失败 ${fail}，fileid_map.json 已写出（${Object.keys(fileids).length} 条）`)
})().catch(e => { console.error('FATAL', e.message); process.exit(1) })
