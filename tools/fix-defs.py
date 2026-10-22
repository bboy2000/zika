# -*- coding: utf-8 -*-
"""
释义补抓：只补 build-defs.py 抓失败的字。

搜狗汉语单 IP 高频请求后会返回 status=1（空），此时百度通常也一起限。
限流是时间窗口型的，过一段时间自己会恢复，所以这里做「轮询等它恢复」：
每轮把所有缺的字试一遍，还有失败就歇 4 分钟再来，直到补齐或超过总时限。

用法：
  python tools/fix-defs.py            # 默认最多等 60 分钟
  python tools/fix-defs.py --max 180  # 最多等 180 分钟
"""
import json
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(tempfile.gettempdir(), 'zika-defs-raw')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')


def fetch_sogou(ch):
    url = 'https://hanyu.sogou.com/api/hanyu/result?query=%s' % urllib.parse.quote(ch)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA,
                                                  'Referer': 'https://hanyu.sogou.com/'})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        if d.get('status') != 0:
            return None, 'throttled'
        items = d.get('data', {}).get('resultData', {}).get('shiyiBase') or []
        out = [{'pinyin': (b.get('pinyin') or '').strip(), 'html': b.get('shiyiHtml') or ''}
               for b in items]
        out = [x for x in out if x['html']]
        return (out, 'sogou') if out else (None, 'empty')
    except Exception as e:
        return None, 'exc:%s' % str(e)[:40]


def fetch_baidu(ch):
    url = ('https://hanyu.baidu.com/hanyu/ajax/search_list?wd=%s&type=1&pn=0&pz=3'
           % urllib.parse.quote(ch))
    try:
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(url, headers={'User-Agent': UA}), timeout=20))
        for it in d.get('ret_array', []):
            if it.get('type') and 'word' in it['type'] and (it.get('name') or [''])[0] == ch:
                out = []
                for g in (it.get('add_mean') or []):
                    htm = ''.join('<p>%s</p>' % x for x in (g.get('definition') or []))
                    if htm:
                        out.append({'pinyin': (g.get('pinyin') or '').strip(), 'html': htm})
                return (out, 'baidu') if out else (None, 'empty')
        return None, 'throttled'
    except Exception as e:
        return None, 'exc:%s' % str(e)[:40]


def main():
    maxmin = 60
    if '--max' in sys.argv:
        maxmin = int(sys.argv[sys.argv.index('--max') + 1])

    src = json.load(open(os.path.join(ROOT, 'public', 'chars.json'), encoding='utf-8'))
    chars = []
    for bid in src['order']:
        for name, items in src['books'][bid]['lessons']:
            for it in items:
                if it[0] not in chars:
                    chars.append(it[0])

    os.makedirs(CACHE, exist_ok=True)
    deadline = time.time() + maxmin * 60
    rnd = 0
    while True:
        rnd += 1
        miss = [c for c in chars if not os.path.exists(os.path.join(CACHE, '%x.json' % ord(c)))]
        if not miss:
            print('全部补齐 ✅')
            return
        print('[第 %d 轮] 缺 %d 字，开始试探' % (rnd, len(miss)))
        ok = 0
        throttle_hits = 0
        for i, ch in enumerate(miss, 1):
            items, via = fetch_sogou(ch)
            if items is None:
                if via == 'throttled':
                    throttle_hits += 1
                    # 连续被限就别硬刷了，直接等窗口
                    if throttle_hits >= 5:
                        print('  连续 5 次被限，本轮停止')
                        break
                items, via = fetch_baidu(ch)
                if items is None:
                    continue
            json.dump({'via': via, 'items': items},
                      open(os.path.join(CACHE, '%x.json' % ord(ch)), 'w', encoding='utf-8'),
                      ensure_ascii=False)
            ok += 1
            throttle_hits = 0
            time.sleep(1.2)
        left = len([c for c in chars
                    if not os.path.exists(os.path.join(CACHE, '%x.json' % ord(c)))])
        print('  本轮补到 %d 字，仍缺 %d 字' % (ok, left))
        if left == 0:
            print('全部补齐 ✅')
            return
        if time.time() > deadline:
            print('超过 %d 分钟时限，还剩 %d 字未补，明天再跑一次即可' % (maxmin, left))
            return
        wait = 240 if ok == 0 else 90
        print('  歇 %d 秒后再试\n' % wait)
        time.sleep(wait)


if __name__ == '__main__':
    main()
