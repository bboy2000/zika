# -*- coding: utf-8 -*-
"""
百度汉语补抓（低速率、拟人节奏）—— 给 build-defs.py 的缓存目录补料

为什么不复用 fix-defs.py 的搜狗通道：
  搜狗对本机 IP 已封控，轮询 1.5 小时只补到 1 字。百度单 IP 短时连发 7 次也会限，
  但那是"频次"限，不是"IP 拉黑"——把速率压到人点页面的水平就能持续跑。

拟人策略（照真实用户翻字典的节奏）：
  1. 先 GET 首页拿 BAIDUID cookie，再带着 cookie 打接口，不是裸请求接口
  2. 每次请求间隔 5~12 秒随机（真人不会每 0.3 秒查一个字）
  3. 每 7~11 个字停下来歇 45~100 秒（看完一屏再查下一个）
  4. 触发限流就指数退避 90→180→360 秒，连撞 3 次直接收工，进度保留下次续跑
  5. 同一会话固定 UA，不来回换指纹

用法：
  python tools/fetch-baidu.py --test 5     # 先试 5 个看通不通
  python tools/fetch-baidu.py              # 补齐所有还缺缓存的字（断点续跑）
  python tools/fetch-baidu.py --chars 丹典军  # 只跑指定字

抓完要重组装（脚本会自动调一次）：
  python tools/build-defs.py --no-fetch
"""
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time

import requests

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(tempfile.gettempdir(), 'zika-defs-raw')
PY = sys.executable

# 固定一套"像本机浏览器"的指纹，整轮不换
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')

HEADERS = {
    'User-Agent': UA,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://hanyu.baidu.com/',
    'Connection': 'keep-alive',
}

API = 'https://hanyu.baidu.com/hanyu/ajax/search_list?wd=%s&type=1&pn=0&pz=3'
HOME = 'https://hanyu.baidu.com/'


def log(msg):
    print(msg, flush=True)


def new_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    # 先像人一样打开首页，拿到 BAIDUID 再查字
    try:
        s.get(HOME, timeout=20,
              headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
        log('  已进入百度汉语首页，cookie: %s' % (', '.join(s.cookies.keys()) or '无'))
    except Exception as e:
        log('  首页打不开（继续尝试接口）：%s' % str(e)[:60])
    return s


def grab(s, ch):
    """返回 (items, status)。status: ok / throttle / notfound / error"""
    url = API % requests.utils.quote(ch)
    try:
        r = s.get(url, timeout=20)
    except Exception as e:
        return None, 'error:%s' % str(e)[:50]

    if r.status_code in (403, 429):
        return None, 'throttle:http%d' % r.status_code
    if r.status_code != 200:
        return None, 'error:http%d' % r.status_code

    try:
        d = r.json()
    except Exception:
        # 返回了 HTML（通常是反爬验证页）
        return None, 'throttle:not-json'

    arr = d.get('ret_array')
    if arr is None:
        return None, 'throttle:no-array'
    if not arr:
        return None, 'throttle:empty-array'

    for it in arr:
        if 'word' not in (it.get('type') or ''):
            continue
        if (it.get('name') or [''])[0] != ch:
            continue
        out = []
        for g in (it.get('add_mean') or []):
            htm = ''.join('<p>%s</p>' % x for x in (g.get('definition') or []))
            if htm:
                out.append({'pinyin': (g.get('pinyin') or '').strip(), 'html': htm})
        if out:
            return out, 'ok'
        return None, 'notfound:add_mean空'
    return None, 'notfound:无单字词条'


def is_meaningful(items, ch):
    """全是「见〖X〗」「姓。」的条目等于没释义，别浪费缓存名额"""
    if not items:
        return False
    for b in items:
        t = re.sub(r'<[^>]+>', '', b['html'])
        t = re.sub(r'\s+', '', t)
        t = re.sub(r'^\d+[.、]', '', t)
        if not t:
            continue
        if re.match(r'^见[〖〔（(]', t):
            continue
        if re.match(r'^[姓同古通]', t) and len(t) < 6:
            continue
        return True
    return False


def main():
    args = sys.argv[1:]
    limit = 0
    if '--test' in args:
        limit = int(args[args.index('--test') + 1])
    only = None
    if '--chars' in args:
        only = args[args.index('--chars') + 1]

    src = json.load(open(os.path.join(ROOT, 'public', 'chars.json'), encoding='utf-8'))
    chars = []
    for bid in src['order']:
        for name, items in src['books'][bid]['lessons']:
            for it in items:
                if it[0] not in chars:
                    chars.append(it[0])

    os.makedirs(CACHE, exist_ok=True)
    cf = lambda c: os.path.join(CACHE, '%x.json' % ord(c))

    if only:
        todo = [c for c in only if c in chars]
    else:
        todo = [c for c in chars if not os.path.exists(cf(c))]
    if limit:
        todo = todo[:limit]

    if not todo:
        log('没有要抓的字')
        return

    # 已有缓存但洗完为空的那批，也要重抓一次（搜狗给的是「见〖X〗」）
    log('本轮待抓 %d 字：%s' % (len(todo), ''.join(todo)))

    s = new_session()
    ok, throttle, notfound, err = 0, 0, 0, 0
    misses = []
    hits = 0                 # 连续限流次数
    t0 = time.time()

    for i, ch in enumerate(todo, 1):
        items, st = grab(s, ch)
        if st == 'ok' and items and is_meaningful(items, ch):
            json.dump({'via': 'baidu', 'items': items}, open(cf(ch), 'w', encoding='utf-8'),
                      ensure_ascii=False)
            ok += 1
            hits = 0
            log('  [%d/%d] %s ✅ %d 组读音' % (i, len(todo), ch, len(items)))
        elif st == 'ok' and items:
            # 抓到了但全是「见〖X〗」：不写缓存，留给人工表
            notfound += 1
            misses.append((ch, '仅交叉引用'))
            log('  [%d/%d] %s ○ 只有交叉引用' % (i, len(todo), ch))
        elif st.startswith('throttle'):
            hits += 1
            throttle += 1
            wait = min(360, 90 * (2 ** (hits - 1)))
            log('  [%d/%d] %s ⚠ 限流(%s)，等 %ds' % (i, len(todo), ch, st.split(':')[1], wait))
            time.sleep(wait)
            if hits >= 3:
                log('\n连撞 3 次限流，先收工。已补 %d 字，下次续跑。' % ok)
                break
            continue
        else:
            err += 1
            misses.append((ch, st))
            log('  [%d/%d] %s ✗ %s' % (i, len(todo), ch, st))

        # 拟人节奏：正常间隔 + 周期性长歇
        if i < len(todo):
            if i % random.randint(7, 11) == 0:
                rest = random.randint(45, 100)
                log('  …… 歇 %d 秒' % rest)
                time.sleep(rest)
            else:
                time.sleep(random.uniform(5, 12))

    el = time.time() - t0
    log('\n完成：成功 %d / 限流 %d / 无有效释义 %d / 出错 %d，耗时 %.0f 分'
        % (ok, throttle, notfound, err, el / 60))
    if misses:
        log('未取到：%s' % '、'.join('%s(%s)' % x for x in misses))

    if ok:
        log('\n重组装 defs_v2.json …')
        subprocess.run([PY, os.path.join(ROOT, 'tools', 'build-defs.py'), '--no-fetch'],
                       cwd=ROOT)


if __name__ == '__main__':
    main()
