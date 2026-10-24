# -*- coding: utf-8 -*-
"""
P3 发音：Edge TTS 晓晓音色全量自合成（方案 5.4，v1.04 定案）

- 语速全库 -15%（面向小学生听读，实测自然不僵硬）
- 按条目合成：单字读音（主库 2307 + 多音字非本课读音）+ 组词整词（天然连贯，不逐字拼接）
- 输出 audio_build/*.mp3 + audio_build/audio_map.json（key -> 文件名），云开发开通后
  按 map 逐条上传云存储并回填 fileID，运行时不依赖合成接口
- 断点续传：已存在且 >= MIN_BYTES 的文件直接跳过，中断重跑即可
- 礼貌限速：3 并发 + 每条 0.2~0.5s 抖动；连续 6 次失败自动停（网络级故障别硬刷）

用法：
  python tools/synth-audio.py --limit 40     # 小批量试跑（清单前 40 条）
  python tools/synth-audio.py                # 全量（断点续跑，可反复执行）
  python tools/synth-audio.py --report       # 只统计清单与已完成数，不出网
"""
import asyncio
import hashlib
import json
import os
import random
import re
import sys
import time

import edge_tts

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(ROOT), 'audio_build')   # E:/字卡项目/audio_build
MAP = os.path.join(OUT, 'audio_map.json')

VOICE = 'zh-CN-XiaoxiaoNeural'
RATE = '-15%'
CONCURRENCY = 3
MIN_BYTES = 1200            # 小于这个大小的 mp3 视为坏文件（单字正常 3~10KB）
FAIL_STOP = 6               # 连续失败 N 次停机

TONEMAP = {'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
           'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
           'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
           'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
           'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
           'ǖ': ('v', 1), 'ǘ': ('v', 2), 'ǚ': ('v', 3), 'ǜ': ('v', 4),
           'ü': ('v', 0)}


def tone3_slug(py):
    """带调拼音 -> 数字调 slug，与 multi_v2.json 的 tone3 完全同格式：
    cháng->chang2、lǜ->lv4、轻声 le->le（无后缀）。声调可能标在韵母中间（sān、shàng）。"""
    p = (py or '').strip().lower()
    out = []
    tone = ''
    for c in p:
        if c in TONEMAP:
            b, t = TONEMAP[c]
            out.append(b)
            if t:
                tone = str(t)
        else:
            out.append(c)
    return ''.join(out) + tone


def build_manifest():
    """清单条目：{key, text, kind}，key 即 audio_map 的键"""
    chars = json.load(open(os.path.join(ROOT, 'public', 'chars.json'), encoding='utf-8'))
    multi = json.load(open(os.path.join(ROOT, 'mp', 'static', 'data', 'multi_v2.json'),
                           encoding='utf-8'))
    items = {}
    order = []

    def add(key, text, kind):
        if key not in items:
            items[key] = {'key': key, 'text': text, 'kind': kind}
            order.append(key)

    # 1) 单字本课读音（2307 字，跨册同字异音自动多列）
    for bid in chars['order']:
        for name, les in chars['books'][bid]['lessons']:
            for ch, py, ws in les:
                add('c:%s:%s' % (ch, tone3_slug(py)), ch, 'char')
                for w in ws:
                    add('w:' + w, w, 'word')
    # 2) 多音字读音（本课读音已被上面 add 过会自动去重；补的是非本课读音）
    #    注意：多音字条目的组词走的是 multi_v2 的 words（与主库同一套，重叠自动去重）
    for ch, rs in multi['chars'].items():
        for r in rs:
            add('c:%s:%s' % (ch, r['tone3']), ch, 'char')
            for w in (r.get('words') or []):
                add('w:' + w, w, 'word')

    return [items[k] for k in order]


def fname(item):
    if item['kind'] == 'char':
        ch, t3 = item['key'].split(':')[1:]
        return 'c_%04x_%s.mp3' % (ord(ch), t3)
    return 'w_%s.mp3' % hashlib.md5(item['text'].encode('utf-8')).hexdigest()[:8]


async def synth_one(sem, item, path, stat, fail_counter):
    async with sem:
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(item['text'], voice=VOICE, rate=RATE)
                await c.save(path)
                if os.path.getsize(path) >= MIN_BYTES:
                    stat['ok'] += 1
                    return True
                os.remove(path)
                stat['short'] += 1
            except Exception as e:
                stat['err'] += 1
                fail_counter['now'] += 1
                if attempt == 2:
                    print('  ✗ %s(%s) %s' % (item['text'], item['key'], str(e)[:60]), flush=True)
                    return False
            await asyncio.sleep(0.5 + attempt)
        fail_counter['now'] += 1
        return False


async def run(todo, stat):
    sem = asyncio.Semaphore(CONCURRENCY)
    fail_counter = {'now': 0}
    t0 = time.time()
    for i, item in enumerate(todo, 1):
        if fail_counter['now'] >= FAIL_STOP:
            print('\n连续失败 %d 次，自动停机。已合成 %d/%d，重跑续传' % (FAIL_STOP, stat['ok'], len(todo)))
            return False
        fail_counter['now'] = 0
        path = os.path.join(OUT, fname(item))
        if os.path.exists(path) and os.path.getsize(path) >= MIN_BYTES:
            stat['skip'] += 1
            continue
        await synth_one(sem, item, path, stat, fail_counter)
        if i % 200 == 0:
            el = time.time() - t0
            left = len(todo) - i
            print('  %d/%d  ok=%d skip=%d err=%d  %.0fs  剩约 %.0f 分'
                  % (i, len(todo), stat['ok'], stat['skip'], stat['err'], el,
                     left * el / max(i, 1) / 60), flush=True)
        await asyncio.sleep(random.uniform(0.2, 0.5))
    return True


def main():
    args = sys.argv[1:]
    limit = 0
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    report_only = '--report' in args

    manifest = build_manifest()
    os.makedirs(OUT, exist_ok=True)
    done = len([f for f in os.listdir(OUT) if f.endswith('.mp3')])
    print('清单 %d 条（单字读音 + 组词整词）｜已完成 %d' % (len(manifest), done))
    kc = len([x for x in manifest if x['kind'] == 'char'])
    print('  其中 单字读音 %d / 组词 %d' % (kc, len(manifest) - kc))

    if report_only:
        return

    todo = manifest if not limit else manifest[:limit]
    stat = {'ok': 0, 'skip': 0, 'err': 0, 'short': 0}
    finished = asyncio.run(run(todo, stat))

    # 写 map：key -> {file, text, kind}
    mp_ = {}
    for item in manifest:
        p = os.path.join(OUT, fname(item))
        if os.path.exists(p) and os.path.getsize(p) >= MIN_BYTES:
            mp_[item['key']] = {'file': fname(item), 'text': item['text'], 'kind': item['kind']}
    json.dump({'voice': VOICE, 'rate': RATE, 'built': time.strftime('%Y-%m-%d %H:%M'),
               'entries': mp_},
              open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('audio_map.json 已更新：%d 条' % len(mp_))
    print('统计', stat, '完成' if finished else '未完成（重跑续传）')


if __name__ == '__main__':
    main()
