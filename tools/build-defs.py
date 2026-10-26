# -*- coding: utf-8 -*-
"""
释义重采：搜狗汉语 shiyiBase → 小学生可读短释义，产出 mp/common/data-json/defs_v2.json

为什么重采：旧库 explanations 是古汉语字典抓取残留，2307 字里
  111 字完全缺失、130 条开头带拼音残片（「上」= àng；位置在…）、
  328 条含〈古〉〈引〉〈喻〉字典标记、307 条中文引号错位成「长”」、33 条混入说文解字体例。
  对小学生的可用性是零。

为什么用搜狗不用百度：
  百度 hanyu.baidu.com 的 search_list 接口短时连发 7 次就被限流（返回空 ret_array，
  实测已持续十几分钟不恢复）；搜狗 0.3 秒连发 26 次全部成功。两家的释义是同一上游
  （《现代汉语词典》体例），搜狗的 shiyiHtml 按 <p> 分段自带序号，比百度的
  definition 数组更好解析。百度作为容灾备用。

用法：
  python tools/build-defs.py                # 全量（2307 字，约 15 分钟）
  python tools/build-defs.py --limit 50     # 只跑前 50 个字（调试）
  python tools/build-defs.py --report       # 不出网，只对已有缓存出质检报告

人工定稿：tools/def-override.json
  极常用字的词典释义反而最啰嗦（「大」= 指面积、体积、容量、数量、强度、力量超过一般…），
  这类字手写覆盖，优先级最高。进了该表的字不参与自动采词。
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(os.environ.get('TEMP', '/tmp'), 'zika-defs-raw')
OUT = os.path.join(ROOT, 'mp', 'common', 'data-json', 'defs_v2.json')
OVERRIDE = os.path.join(ROOT, 'tools', 'def-override.json')

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

# ---------- 抓取 ----------

def _get(url, referer=None):
    h = {'User-Agent': UA}
    if referer:
        h['Referer'] = referer
    req = urllib.request.Request(url, headers=h)
    return json.load(urllib.request.urlopen(req, timeout=20))


def fetch_sogou(ch):
    """返回 shiyiBase 列表，元素形如 {pinyin, shiyiHtml, cMore}"""
    url = 'https://hanyu.sogou.com/api/hanyu/result?query=%s' % urllib.parse.quote(ch)
    last = ''
    for i in range(3):
        try:
            d = _get(url, referer='https://hanyu.sogou.com/')
            if d.get('status') != 0:
                time.sleep(0.7 + i * 0.5)
                continue
            items = d.get('data', {}).get('resultData', {}).get('shiyiBase') or []
            # 统一成 {pinyin, html}
            out = [{'pinyin': (b.get('pinyin') or '').strip(),
                    'html': b.get('shiyiHtml') or ''} for b in items]
            out = [x for x in out if x['html']]
            if out:
                return out, 'sogou'
            return None, 'sogou:shiyiBase空'
        except Exception as e:
            time.sleep(0.7 + i * 0.5)
            last = str(e)[:60]
    return None, 'sogou:%s' % last


def fetch_baidu(ch):
    """容灾：百度 add_mean，转成同样的 {pinyin, html} 结构"""
    url = ('https://hanyu.baidu.com/hanyu/ajax/search_list?wd=%s&type=1&pn=0&pz=3'
           % urllib.parse.quote(ch))
    last = ''
    for i in range(2):
        try:
            d = _get(url)
            for it in d.get('ret_array', []):
                if it.get('type') and 'word' in it['type'] and (it.get('name') or [''])[0] == ch:
                    out = []
                    for g in (it.get('add_mean') or []):
                        ps = [g.get('pinyin') or '']
                        ps += [''] * 0
                        htm = ''.join('<p>%s</p>' % x for x in (g.get('definition') or []))
                        if htm:
                            out.append({'pinyin': (g.get('pinyin') or '').strip(), 'html': htm})
                    if out:
                        return out, 'baidu'
                    return None, 'baidu:add_mean空'
            return None, 'baidu:未命中'
        except Exception as e:
            time.sleep(1.2 + i)
            last = str(e)[:60]
    return None, 'baidu:%s' % last


# ---------- 清洗 ----------

PYCH = 'a-zA-ZàáǎāèéěēìíǐīòóǒōùúǔūǖǘǚǜüÀÁǍĀÈÉĚĒÌÍǏĪÒÓǑŌÙÚǓŪǕǗǙǛ'
DROP_EXACT = re.compile(
    r'^（?[%s·]*）?(姓|见|同|古|通|用于地名|用于人名)[。：]?$' % PYCH)
DROP_HINT = re.compile(r'旧读|的又音|韵母|收音|〈古〉|〈引〉|〈喻〉|〈表〉|〈方〉|〈书〉|“傢”')


def strip_tags(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    return (s.replace('&amp;', '&').replace('&quot;', '"')
             .replace('&nbsp;', '').replace('&lt;', '“').replace('&gt;', '”'))


def norm(s):
    s = re.sub(r'[「『]', '“', s)
    s = re.sub(r'[」』]', '”', s)
    s = s.replace('(', '（').replace(')', '）')
    s = s.replace(',', '，').replace(';', '；').replace(':', '：')
    return re.sub(r'\s+', '', s)


def clean_seg(s, ch):
    """把一条词典义项洗成给孩子看的主干。顺序有讲究，别随意调。"""
    s = strip_tags(s)
    # (1) 条序号必须在字母子项之前认：原文是「1.a）在」，先去掉「1.」才认得出「a）」
    s = re.sub(r'^\d+[\.、．]\s*', '', s)
    # (2) 词头标记先删，否则「〔～璃〕a.…」认不出条首的「a.」
    s = re.sub(r'〔[^〕]*〕', '', s)
    # (3) 字母子项：条首「a）」「a.」去掉、正文保留；「。a）…」之后整段砍掉
    s = re.sub(r'。[a-zA-Zａ-ｚＡ-Ｚ][）).．].*$', '', s)
    s = re.sub(r'^[a-zA-Zａ-ｚＡ-Ｚ][）).．、]\s*', '', s)
    s = re.sub(r'[；;][a-zA-Zａ-ｚＡ-Ｚ][）).．].*$', '', s)      # 中段子项「；b.旧称」
    s = re.sub(r'[\[［][^\]］]*[\]］]', '', s)
    s = re.sub(r'[\[\]［］]', '', s)
    # (4) 词性标记 〈动〉〈名〉
    s = re.sub(r'〈[动名形副助量代介连叹数象声语气]〉', '', s)
    # (5) 交叉引用：见〖数字〗、【蝙蝠】见biān
    s = re.sub(r'见?〖[^〗]*〗', '', s)
    s = re.sub(r'【[^】]*】见.*$', '', s)
    # (6) 括号内超过 12 字的补充说明，对孩子是噪音
    s = re.sub(r'[（(][^）)]{13,}[）)]', '', s)
    # (7) 注音括注与又读音
    s = re.sub(r'[（(][%s·]+[）)]' % PYCH, '', s)
    s = re.sub(r'[（(][旧又还]{0,2}[读音][^）)]{1,12}[）)]', '', s)
    # (8) 代字符 ～ 还原成本字
    s = s.replace('～', ch).replace('~', ch)
    # (9) 标点归一（此后才是全角）
    s = norm(s)
    # (10) 例词在「：」后面，只留释义主干
    s = s.split('：')[0]
    # (11) 句号并逗号，收拾首尾
    s = s.replace('。', '，')
    s = re.sub(r'^[，；]+', '', s)
    s = re.sub(r'[，；]+$', '', s)
    s = re.sub(r'，+', '，', s)
    return s.strip()


def shorten(t, limit=26):
    if len(t) <= limit:
        return t
    m = re.search(r'^(.{4,}?）)', t)
    if m and len(m.group(1)) <= limit + 4:
        return m.group(1)
    m = re.match(r'^(.{6,}?)[；，]', t)
    if m and 8 <= len(m.group(1)) <= limit:
        return m.group(1)
    cut = t[:limit]
    # 截断点落在括号内会把括号切断（「…状态（跟“松」），把未闭合部分整段去掉
    if cut.count('（') > cut.count('）'):
        cut = cut[:cut.rindex('（')]
    return cut.rstrip('，、；') + '…'


def build_defs(items, ch, py, want=2):
    pys = [x['pinyin'] for x in items if x['pinyin']]
    picked = []
    long_ones = []
    for block in items:
        if py and block['pinyin'] and block['pinyin'] != py:
            continue
        # 搜狗有三种排版：<dd><p>…</p></dd>、<ol><li>…</li></ol>、（两者混用）
        segs = re.findall(r'<p[^>]*>(.*?)</p>', block['html'], re.S)
        if not segs:
            segs = re.findall(r'<li[^>]*>(.*?)</li>', block['html'], re.S)
        if not segs:
            segs = [block['html']]
        for p in segs:
            main = re.split(r'<span', p)[0]
            t = clean_seg(main, ch)
            if not t:
                continue
            if DROP_EXACT.match(t) or DROP_HINT.search(t):
                continue
            if len(t) > 32:
                # 词典第一条通常就是本义，不能因为长就丢——否则「电」会取到「触电」、
                # 「牛」会取到「比喻固执」。本义截断也比取次要义项强。
                if not picked:
                    picked.append(shorten(t))
                else:
                    long_ones.append(t)
                continue
            picked.append(shorten(t))
            if len(picked) >= want:
                return picked, pys
    if len(picked) < want and long_ones:
        picked.append(shorten(long_ones[0]))
    return picked, pys


# ---------- 旧库清洗（兜底） ----------

def clean_old(s, ch):
    if not s:
        return []
    s = s.split('；')[0]
    s = re.sub(r'^[a-zA-Zàáǎāèéěēìíǐīòóǒōùúǔūǖǘǚǜ]+\s*[；;]\s*', '', s)
    s = re.sub(r'〈[古引喻表形音义]〉', '', s)
    s = re.sub(r'[“”"]', '', s)
    s = re.sub(r'（[^）]{13,}）', '', s)
    s = norm(s)
    s = s.replace('。', '，')
    s = re.sub(r'[，；]+$', '', s)
    if len(s) < 4 or re.search(r'象形|本义|甲骨文|小篆|形声|指事|会意', s):
        return []
    # 旧库质量不可靠，洗完还带交叉引用/拼音/方括号的一律不要——宁可不显示也不给孩子看乱码
    if re.search(r'[【】〖〗㈠-㈩\[\]［］]', s) or re.search(r'[a-zA-Z]', s):
        return []
    if re.match(r'^[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', s):
        return []
    return [shorten(s, 26)]


# ---------- 主流程 ----------

def main():
    args = sys.argv[1:]
    limit = 0
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    # --no-fetch：只按已有缓存重新组装（改了清洗规则、不想再出网时用）
    report_only = '--report' in args or '--no-fetch' in args

    src = json.load(open(os.path.join(ROOT, 'public', 'chars.json'), encoding='utf-8'))
    lesson_py = {}
    chars = []
    for bid in src['order']:
        for name, items in src['books'][bid]['lessons']:
            for it in items:
                if it[0] not in lesson_py:
                    lesson_py[it[0]] = it[1]
                    chars.append(it[0])

    override = {}
    if os.path.exists(OVERRIDE):
        override = json.load(open(OVERRIDE, encoding='utf-8')).get('chars', {})

    os.makedirs(CACHE, exist_ok=True)
    if not report_only:
        todo = [c for c in chars if c not in override]
        if limit:
            todo = todo[:limit]
        print('待采 %d 字（人工定稿 %d 字跳过）' % (len(todo), len(override)))

        stat = {'sogou': 0, 'baidu': 0, 'cached': 0, 'fail': 0}
        fails = []
        t0 = time.time()
        for i, ch in enumerate(todo, 1):
            cf = os.path.join(CACHE, '%x.json' % ord(ch))
            if os.path.exists(cf):
                stat['cached'] += 1
                continue
            items, via = fetch_sogou(ch)
            if items is None:
                items, via2 = fetch_baidu(ch)
                if items is None:
                    stat['fail'] += 1
                    fails.append((ch, via, via2))
                    print('  [%d/%d] %s 失败 %s / %s' % (i, len(todo), ch, via, via2))
                    continue
                via = 'baidu'
            json.dump({'via': via, 'items': items}, open(cf, 'w', encoding='utf-8'),
                      ensure_ascii=False)
            stat[via] += 1
            time.sleep(0.3)
            if i % 100 == 0:
                el = time.time() - t0
                print('  %d/%d  已用 %.0fs  成功 sogou=%d baidu=%d 失败=%d'
                      % (i, len(todo), el, stat['sogou'], stat['baidu'], stat['fail']))
        print('抓取完成：%s  耗时 %.0fs' % (stat, time.time() - t0))
        if fails:
            print('失败字：', ''.join(x[0] for x in fails))

    # 组装
    out = {}
    q = {'auto': 0, 'override': 0, 'fallback_old': 0, 'empty': 0, 'py_mismatch': 0}
    problems = []
    for ch in chars:
        py = lesson_py.get(ch, '')
        if ch in override:
            d = override[ch]
            defs = d['defs'] if isinstance(d, dict) else d
            p2 = (d.get('py') if isinstance(d, dict) else None) or py
            out[ch] = {'py': p2, 'defs': defs, 'src': 'override'}
            q['override'] += 1
            continue
        cf = os.path.join(CACHE, '%x.json' % ord(ch))
        if not os.path.exists(cf):
            out[ch] = {'py': py, 'defs': [], 'src': 'missing'}
            q['empty'] += 1
            problems.append((ch, '无缓存'))
            continue
        raw = json.load(open(cf, encoding='utf-8'))
        defs, pys = build_defs(raw['items'], ch, py)
        srcv = raw['via']
        if defs:
            q['auto'] += 1
        else:
            if py and pys and py not in pys:
                q['py_mismatch'] += 1
                problems.append((ch, '本课读音 %s 不在源数据 %s' % (py, pys)))
            old = clean_old(src['explanations'].get(ch), ch)
            if old:
                defs, srcv = old, 'old'
                q['fallback_old'] += 1
            else:
                q['empty'] += 1
                problems.append((ch, '清洗后为空且旧库不可用'))
        out[ch] = {'py': py, 'defs': defs, 'src': srcv}

    doc = {
        'version': 'v1',
        'built': time.strftime('%Y-%m-%d'),
        'source': 'sogou:shiyiBase (百度 add_mean 容灾)',
        'total': len(out),
        'chars': out,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('\n写出 %s' % OUT)
    print('统计：', q)
    have = len([1 for v in out.values() if v['defs']])
    print('有释义 %d / %d（%.1f%%）' % (have, len(out), have * 100.0 / len(out)))

    # 质检
    bad = []
    for ch, v in out.items():
        for d in v['defs']:
            if re.search(r'[〈〉〖〗∪『』\[\]]', d):
                bad.append((ch, '残留字典符号', d))
            if re.search(r'[a-zA-Z][）)]', d):
                bad.append((ch, '残留字母子项', d))
            if d.count('“') != d.count('”'):
                bad.append((ch, '引号不配对', d))
            if len(d) > 32:
                bad.append((ch, '过长 %d 字' % len(d), d))
            if re.search(r'[a-zA-Zàáǎāèéěēìíǐīòóǒōùúǔū]', d) \
                    and not re.search(r'符号[A-Za-z]+', d):
                bad.append((ch, '含拼音残留', d))
    print('质检异常 %d 条' % len(bad))
    for x in bad[:15]:
        print('  ', x)

    if problems:
        pf = os.path.join(ROOT, 'design', 'defs-problems.txt')
        os.makedirs(os.path.dirname(pf), exist_ok=True)
        with open(pf, 'w', encoding='utf-8') as f:
            for ch, why in problems:
                f.write('%s\t%s\n' % (ch, why))
        print('问题清单写到 %s（%d 条）' % (pf, len(problems)))


if __name__ == '__main__':
    main()
