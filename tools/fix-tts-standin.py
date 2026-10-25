# -*- coding: utf-8 -*-
"""
P3-2 读音纠错：多音字单字音频的同音替身重合成（方案 5.4 预留）

问题：Edge TTS 读单字按自家词典走默认读音。多音字的非默认读音会被读错
     （例：个 gě 三声被读成 gè 四声）。

方案：用「读音完全相同且只有这一个读音」的字替身去合成那条音频——
     替身是单音字，Edge 不可能读错；替身只出声不上屏，孩子看不到。

替身挑选：
- 候选 = pinyin-data（4.4 万单字）里 tone3 与目标读音完全相同的单读音字
- 排除原字、排除多音字（默认读音不可控）
- 按 jieba 单字词频取最高（保证是常用字，Edge 词典稳定）

输出：
- audio_build/standin_map.json   key -> 替身字（留档，重跑全量合成时不丢）
- 覆盖 audio_build/c_XXXX_t3.mp3 并更新 audio_map.json 的 text 字段
- 找不到替身的读音原样保留，打印清单留给人工听审

用法：
  python tools/fix-tts-standin.py --plan     # 只算替身清单，不出网
  python tools/fix-tts-standin.py            # 重合成（只合成被替换的那批）
"""
import asyncio
import hashlib
import json
import os
import sys
import time

import edge_tts

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(ROOT), 'audio_build')
MAP = os.path.join(OUT, 'audio_map.json')
STANDIN_MAP = os.path.join(OUT, 'standin_map.json')
CHARDATA = os.path.join(ROOT, 'tools', 'pinyin-data.txt')
JIEBA = os.path.join(ROOT, 'tools', 'jieba_dict.txt')
MULTI = os.path.join(ROOT, 'mp', 'static', 'data', 'multi_v2.json')

VOICE = 'zh-CN-XiaoxiaoNeural'
RATE = '-15%'
CONCURRENCY = 3
MIN_BYTES = 1200

# 与 synth-audio.py 的 tone3_slug 同一套（带调 -> 数字调 slug）
TONEMAP = {'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
           'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
           'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
           'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
           'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
           'ǖ': ('v', 1), 'ǘ': ('v', 2), 'ǚ': ('v', 3), 'ǜ': ('v', 4),
           'ü': ('v', 0)}


def tone3_slug(py):
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


def gb2312_ok(ch):
    """常用字才配当替身：生僻字（GB2312 外）Edge 词典可能没有，读了白读"""
    try:
        ch.encode('gb2312')
        return True
    except UnicodeEncodeError:
        return False


def load_single_readings():
    """pinyin-data -> {tone3: [(char, freq)]}，只收单读音字；
    替身硬条件：jieba 词频 >= 10（常用度）+ GB2312 内（Edge 词典稳）"""
    freq = {}
    for line in open(JIEBA, encoding='utf-8'):
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 1:
            try:
                freq[parts[0]] = max(freq.get(parts[0], 0), int(parts[1]))
            except ValueError:
                pass

    table = {}
    for line in open(CHARDATA, encoding='utf-8'):
        if line.startswith('#') or ':' not in line:
            continue
        head, tail = line.split(':', 1)
        if not head.startswith('U+'):
            continue
        pys = tail.split('#')[0].split()
        if len(pys) != 1:
            continue  # 多读音字不当替身
        ch = chr(int(head[2:], 16))
        if freq.get(ch, 0) < 10 or not gb2312_ok(ch):
            continue
        t3 = tone3_slug(pys[0])
        table.setdefault(t3, []).append((ch, freq.get(ch, 0)))
    for t3 in table:
        table[t3].sort(key=lambda x: -x[1])
    return table


def build_plan():
    multi = json.load(open(MULTI, encoding='utf-8'))['chars']
    table = load_single_readings()
    plan = {}   # key -> {'ch','tone3','standin','freq'}
    miss = []   # 找不到替身的
    for ch, rs in multi.items():
        for r in rs:
            t3 = r['tone3']
            key = 'c:%s:%s' % (ch, t3)
            cands = [(c, f) for c, f in table.get(t3, []) if c != ch]
            if not cands:
                miss.append((ch, r['py'], t3))
                continue
            standin, f = cands[0]
            plan[key] = {'ch': ch, 'tone3': t3, 'py': r['py'],
                         'standin': standin, 'freq': f}
    return plan, miss


def fname_for(key):
    """替身音频用 _s 后缀的新文件名：不覆盖旧文件（沙箱禁删 + 保留原版可回滚）"""
    ch, t3 = key.split(':')[1:]
    return 'c_%04x_%s_s.mp3' % (ord(ch), t3)


async def synth_one(sem, key, text, path, stat):
    async with sem:
        for attempt in range(3):
            try:
                c = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
                await c.save(path)
                if os.path.getsize(path) >= MIN_BYTES:
                    stat['ok'] += 1
                    return True
                os.remove(path)
                stat['short'] += 1
            except Exception as e:
                stat['err'] += 1
                if attempt == 2:
                    print('  ✗ %s(%s) %s' % (text, key, str(e)[:60]), flush=True)
                    return False
            await asyncio.sleep(0.5 + attempt)
        return False


async def run(todo):
    sem = asyncio.Semaphore(CONCURRENCY)
    stat = {'ok': 0, 'err': 0, 'short': 0}
    t0 = time.time()
    for i, (key, info) in enumerate(todo, 1):
        path = os.path.join(OUT, fname_for(key))
        await synth_one(sem, key, info['standin'], path, stat)
        if i % 50 == 0:
            print('  %d/%d ok=%d err=%d %.0fs' % (i, len(todo), stat['ok'], stat['err'],
                                                  time.time() - t0), flush=True)
        await asyncio.sleep(0.2)
    return stat


def main():
    plan_mode = '--plan' in sys.argv
    plan, miss = build_plan()
    print('多音字读音 %d 条：可替身 %d，无替身 %d' % (len(plan) + len(miss), len(plan), len(miss)))
    if miss:
        print('无替身（原样保留，留人工听审）：')
        for ch, py, t3 in miss:
            print('  %s %s(%s)' % (ch, py, t3))
    if plan_mode:
        for k, v in list(plan.items())[:20]:
            print('  %s  %s(%s) <- 替身「%s」(freq %d)' % (v['ch'], v['py'], v['tone3'],
                                                          v['standin'], v['freq']))
        return

    if not plan:
        print('没有需要替换的读音')
        return

    stat = asyncio.run(run(list(plan.items())))

    # 留档 + 更新 audio_map
    json.dump({'built': time.strftime('%Y-%m-%d %H:%M'),
               'note': '多音字单字音频同音替身（替身字只出声不上屏）',
               'standins': plan},
              open(STANDIN_MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    m = json.load(open(MAP, encoding='utf-8'))
    n = 0
    for key, info in plan.items():
        p = os.path.join(OUT, fname_for(key))
        if key in m['entries'] and os.path.exists(p) and os.path.getsize(p) >= MIN_BYTES:
            m['entries'][key]['file'] = fname_for(key)
            m['entries'][key]['text'] = info['standin']
            m['entries'][key]['standinFor'] = info['ch']
            n += 1
    json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('重合成 ok=%d err=%d short=%d；audio_map 更新 %d 条；standin_map.json 已留档'
          % (stat['ok'], stat['err'], stat['short'], n))


if __name__ == '__main__':
    main()
