# -*- coding: utf-8 -*-
"""
组词重建：把 chars.json 里每字的组词换成小学年龄段能懂的常用词。

策略
1. 候选池        jieba dict.txt（34.9 万词，带词频 + 词性）
2. 硬过滤        长度 2~3 / 排除地名·人名·专名·机构·音译·成语·习语 / 敏感词黑名单
3. 读音校验      pypinyin 取该字在词中的实际读音，必须与本课拼音同音节
                 （声调不同只降权不淘汰，轻声词如「衣裳」需要放宽）
4. 年级加权      ★核心★ 词的用字尽量不超出现学段：一字年级越高扣分越多
                 避免一年级出现「资本、风险、产业」这类成人词汇
5. 排序打分      log(词频) + 双字加分 + 年级加分 + 声调吻合加分 - 三字扣分
6. 人工兜底      OVERRIDE 白名单优先级最高（一年级全部 + 高频多音字）

用法
    python tools/fix-words.py            # 只出报告，不动数据
    python tools/fix-words.py --apply    # 写回 public/chars.json 并重建小程序数据
"""
import json
import math
import os
import sys

from pypinyin import lazy_pinyin, Style

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "public", "chars.json")
JIEBA = os.path.join(ROOT, "tools", "jieba_dict.txt")
REPORT = os.path.join(ROOT, "design", "words-report.md")
REVIEW = os.path.join(ROOT, "design", "words-review.md")

# 地名 / 国名 / 名胜：jieba 常标成 n / s 混淆，靠词表挡
PLACES = set("""
中国 美国 英国 法国 德国 日本 韩国 俄国 苏联 印度 巴西 埃及 希腊 罗马 泰国
越南 朝鲜 蒙古 西班牙 葡萄牙 意大利 加拿大 澳大利亚 俄罗斯 新加坡 马来西亚
北京 上海 天津 重庆 河北 山西 辽宁 吉林 黑龙江 江苏 浙江 安徽 福建 江西
山东 河南 湖北 湖南 广东 海南 四川 贵州 云南 陕西 甘肃 青海 台湾 内蒙古
广西 西藏 宁夏 新疆 香港 澳门 台北 高雄
广州 深圳 杭州 南京 武汉 成都 西安 长沙 沈阳 青岛 大连 厦门 苏州 无锡
宁波 郑州 济南 合肥 福州 昆明 哈尔滨 长春 石家庄 太原 南昌 贵阳 兰州
西宁 银川 拉萨 南宁 海口 呼和浩特 乌鲁木齐 包头 鞍山 抚顺 吉林市
天安门 长城 长江 黄河 泰山 黄山 华山 故乡
""".split())

# 词性分级（jieba 标注本身有噪声：太阳=ns、阳光=nr、明白=nr、你好=l，
# 所以只有「专名/机构/音译」这类硬信号才排除，其余一律降权）
HARD_BAD_POS = {"nz", "nt", "nrt", "nrfg", "nrf"}
SOFT_BAD_POS = {"ns", "nr", "i", "l", "x"}   # 地名/人名/成语/习语/非语素
SOFT_PENALTY = 8.0
# jieba 常把常用词误标成 ns/nr（太阳=ns、阳光=nr、明白=nr），这些词免罚
ALLOW_SOFT = set("""
太阳 阳光 明白 你好 一共 一定 一样 一起 一些 一直 一般 一向 一切 一边 一头 一半
一同 一贯 一心 一时 一早 一流 一流 两下 两家 分工 明明 光明 明天 明日 明智
""".split())

MIN_FREQ = 20            # 词频下限：低于此值基本是人名/地名/生造词的残留
GRADE_PENALTY = 6.0      # 每超出「本字年级+1」一级扣多少分（重罚，逼出低年级词）

# 变调字：一、不 的声调会随下文变化（一起 yi4、不是 bu2），不能拿本课声调硬卡
SANDBOX_CHARS = {"一", "不"}

# 敏感词 / 不适合儿童 / 专名漏网 的手工黑名单
BLACKLIST = {
    # 脏话、贬义、性相关（儿童应用绝不出现）
    "他妈的", "妈的", "混蛋", "王八", "傻瓜", "白痴", "痴呆", "见鬼", "该死",
    "狗日", "走狗", "狗肉", "阴道", "阴部", "性交", "交配", "强奸", "自杀",
    # 专名漏网（词性标错导致没被过滤）
    "义和团", "石首", "六安", "六盘水", "丹东", "鄂西", "当阳",
    "长城", "长江", "黄河", "青山", "吴三桂", "武松", "孔明", "列宁",
    "戴尔", "叶碧秋", "阿拉伯", "太平洋", "意杨",
    "武汉市", "舟曲", "舟山", "仙桃市", "杨桥湖", "汉川", "东湖",
    # 语气词的垃圾组合（jieba 里没有正常搭配）
    "啊哈", "啊呀", "啊呀呀", "呀呀", "天呀", "线呢", "大衣呢", "养呢", "干吗",
    "抄家", "抄本", "歌仔戏", "仔鸡",
    # 政治/成人词汇
    "党员", "全党", "党内", "党建", "党性", "中共", "党委", "支部",
    "寡头", "本级", "长剑", "云盘", "风投", "按揭", "股价", "上市",
    "知青", "千卡", "信用卡", "你老", "鼓吹",
}

# 人工校对表：优先级最高，出现即采用，**不受词库收录与黑名单限制**，只校验读音
# 一年级写字表 300 字全量人工校对；其余年级靠词频 + 年级加权自动选取
OVERRIDE_FILE = os.path.join(ROOT, "tools", "word-override.json")


def load_override():
    if not os.path.exists(OVERRIDE_FILE):
        return {}
    d = json.load(open(OVERRIDE_FILE, encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


OVERRIDE = {}
RELAXED_USED = set()      # 因为严格读音取不满而放宽声调的 (字, 词)


TONE_MAP = {
    "ā": ("a", 1), "á": ("a", 2), "ǎ": ("a", 3), "à": ("a", 4),
    "ē": ("e", 1), "é": ("e", 2), "ě": ("e", 3), "è": ("e", 4),
    "ī": ("i", 1), "í": ("i", 2), "ǐ": ("i", 3), "ì": ("i", 4),
    "ō": ("o", 1), "ó": ("o", 2), "ǒ": ("o", 3), "ò": ("o", 4),
    "ū": ("u", 1), "ú": ("u", 2), "ǔ": ("u", 3), "ù": ("u", 4),
    "ǖ": ("v", 1), "ǘ": ("v", 2), "ǚ": ("v", 3), "ǜ": ("v", 4),
    "ü": ("v", 0), "ń": ("n", 2), "ň": ("n", 3), "ǹ": ("n", 4),
}


def split_lesson_py(py):
    """把带声调拼音拆成 (base, tone)：shàng -> ('shang', 4)；le -> ('le', 0)"""
    base, tone = [], 0
    for ch in py.strip():
        if ch in TONE_MAP:
            b, t = TONE_MAP[ch]
            base.append(b)
            tone = tone or t
        elif ch.isalpha():
            base.append(ch.lower())
    return "".join(base), tone


def load_jieba(path):
    if not os.path.exists(path):
        print("[!] 缺少词库：", path)
        print("    curl -s -o tools/jieba_dict.txt "
              "https://raw.githubusercontent.com/fxsjy/jieba/master/jieba/dict.txt")
        sys.exit(1)
    words = {}
    for line in open(path, encoding="utf-8"):
        p = line.split()
        if len(p) < 2:
            continue
        try:
            freq = int(p[1])
        except ValueError:
            continue
        words[p[0]] = (freq, p[2] if len(p) > 2 else "")
    return words


def build_index(words):
    idx = {}
    for w in words:
        for ch in set(w):
            idx.setdefault(ch, []).append(w)
    return idx


def load_char_grade():
    """字 -> 最早出现的年级（1..6），用于判断「这个词孩子学过没」"""
    grade = {}
    books_dir = os.path.join(ROOT, "mp", "static", "data", "books")
    for fn in sorted(os.listdir(books_dir)):
        if not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(books_dir, fn), encoding="utf-8"))
        label = d["label"]                 # 形如「一年级上册」
        CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
        g = CN.get(label[0], 6)
        for _, items in d["lessons"]:
            for it in items:
                ch = it[0]
                if ch not in grade or g < grade[ch]:
                    grade[ch] = g
    return grade


def reading_of(word, ch, cache={}):
    """取 ch 在 word 中的所有读数，返回 [(base, tone), ...]

    Style.TONE3 输出本身就是「音节+调号数字」（chuang1 / le），
    不能再过一遍带调转写，否则数字会被当成音节的一部分。
    """
    if word not in cache:
        cache[word] = lazy_pinyin(word, style=Style.TONE3,
                                  neutral_tone_with_five=False)
    out = []
    for i, c in enumerate(word):
        if c != ch or i >= len(cache[word]):
            continue
        s = cache[word][i]
        if not s:
            continue
        if s[-1].isdigit():
            out.append((s[:-1].lower(), int(s[-1])))
        else:
            out.append((s.lower(), 0))
    return out


def pick(ch, py, words, idx, grade_of, base_tone, n=3):
    """base_tone: (base, tone) 本课读音"""
    base, tone = base_tone
    g0 = grade_of.get(ch, 6)
    cands, relaxed = [], []

    # 1) 人工校对表：不看词频、不看词库收录、不做读音校验（pypinyin 对拽/茸/颇 等
    #    生僻字的声调标注本身有错，硬校验会误杀人工校对结果）
    #    进了人工表的字**完全由人工表决定**，不再自动补位（否则第 3 个槽位会把
    #    「蒋丽莉」「曹雪芹」这类人名补进来）；写成 [] 表示该字没有常用组词
    if ch in OVERRIDE:
        return [w for w in OVERRIDE[ch] if ch in w]

    # 2) 词频候选
    for w in idx.get(ch, []):
        if w in BLACKLIST or w in PLACES:
            continue
        freq, pos = words[w]
        if freq < MIN_FREQ:
            continue
        if pos in HARD_BAD_POS:
            continue
        if not (2 <= len(w) <= 3):
            continue
        if any(not ("\u4e00" <= c <= "\u9fff") for c in w):
            continue
        r = reading_of(w, ch)
        if not r:
            continue
        hit = [t for b, t in r if b == base]
        if not hit:
            continue
        # 声调必须吻合（音节相同但声调不符 = 选错读音，如 切 qiē→一切、种 zhòng→这种）
        # 例外：一/不 有变调（一起 yi4、不是 bu2），轻声本课（tone=0）不作要求
        tone_bad = False
        if tone and ch not in SANDBOX_CHARS:
            if hit and not any(t == tone for t in hit if t):
                if any(t for t in hit):          # 全是轻声则放行
                    tone_bad = True

        score = math.log10(freq + 1) * 6.0
        if len(w) == 2:
            score += 1.2
        else:
            score -= 4.0        # 小学组词以双字词为主；三字词多为人名地名/术语，重压
        # 年级加权：词的用字超出「本字年级 + 1」越多扣越狠
        over = sum(max(0, grade_of.get(c, 6) - (g0 + 1)) for c in w)
        score -= over * GRADE_PENALTY
        # 词性存疑的降权，但不排除（太阳/阳光/明白都被 jieba 误标）
        if pos in SOFT_BAD_POS:
            score -= SOFT_PENALTY
        # 叠字词（爸爸/妈妈）轻微降权，但不排除
        if len(w) == 2 and w[0] == w[1]:
            score -= 0.4
        # 声调吻合加分
        if tone and tone in hit:
            score += 0.8
        if tone_bad:
            score -= 3.0
            relaxed.append((score, w))
        else:
            cands.append((score, w))

    cands.sort(key=lambda x: (-x[0], len(x[1])))
    out, seen = [], set()
    for _, w in cands:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
        if len(out) >= n:
            break
    # 只有严格读音一个都没取到时，才放宽声调兜底
    # （不为了凑满 3 个而放宽——那会把「张翠山」「裘千仞」这类人名放进来）
    if not out:
        relaxed.sort(key=lambda x: (-x[0], len(x[1])))
        for _, w in relaxed:
            if w in seen or w in out:
                continue
            out.append(w)
            RELAXED_USED.add((ch, w))
            if len(out) >= n:
                break
    return out


def main():
    apply = "--apply" in sys.argv
    words = load_jieba(JIEBA)
    idx = build_index(words)
    grade_of = load_char_grade()
    OVERRIDE.update(load_override())
    src = json.load(open(SRC, encoding="utf-8"))

    multi_chars = set(src.get("multi", {}).keys())
    rows = []
    py_bad = []          # 拼音疑似错误：单音字却与 pypinyin 唯一读音不符

    def check_pinyin(ch, py):
        from pypinyin import pinyin as _py, Style as _S
        variants = _py(ch, style=_S.TONE3, heteronym=True,
                       neutral_tone_with_five=False)
        if not variants or len(variants[0]) != 1:
            return                    # 本就是多音字，跳过
        only = variants[0][0]
        obase = only[:-1] if only[-1].isdigit() else only
        otone = int(only[-1]) if only[-1].isdigit() else 0
        base, tone = split_lesson_py(py)
        if base != obase or (tone and otone and tone != otone):
            py_bad.append((ch, py, only))

    def walk(book_label, items):
        for it in items:
            ch, py, cur = it[0], it[1], it[2]
            old = list(cur or [])
            check_pinyin(ch, py)
            bt = split_lesson_py(py)  # 本课读音（数据已给定），拆成 base + 调号
            new = pick(ch, py, words, idx, grade_of, bt)
            rows.append({"book": book_label, "ch": ch, "py": py,
                         "old": old, "new": new,
                         "multi": ch in multi_chars})
            it[2] = new

    for bid in src["order"]:
        book = src["books"][bid]
        label = src["labels"].get(bid, bid)
        for _, items in book["lessons"]:
            walk(label, items)

    changed = sum(1 for r in rows if r["old"] != r["new"])
    filled = sum(1 for r in rows if not r["old"] and r["new"])
    empty = [r for r in rows if not r["new"]]

    if apply:
        with open(SRC, "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False, separators=(",", ":"))
        print("[写回]", SRC)
        # 同步重建小程序端 12 册 + dict.json
        rc = os.system(f'"{sys.executable}" "{os.path.join(ROOT, "tools", "build-data.py")}"')
        print("[重建小程序数据] 退出码", rc)

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("# 组词重建报告\n\n")
        f.write(f"- 总条目 {len(rows)}，改动 {changed} 条"
                f"（{changed/len(rows)*100:.1f}%）\n")
        f.write(f"- 原无组词、本次补上 {filled} 条\n")
        f.write(f"- 仍未取到词 {len(empty)} 条\n\n")
        f.write("## 全量对照\n\n| 册 | 字 | 拼音 | 原组词 | 新组词 |\n|---|---|---|---|---|\n")
        for r in rows:
            o = "、".join(r["old"]) if r["old"] else "—"
            n = "、".join(r["new"]) if r["new"] else "**无**"
            m = "" if r["old"] == r["new"] else " ⬅"
            f.write(f"| {r['book']} | {r['ch']} | {r['py']} | {o} | {n}{m} |\n")

    # 复核清单：一年级全部 + 全部多音字
    with open(REVIEW, "w", encoding="utf-8") as f:
        f.write("# 组词待复核清单\n\n## 一、一年级全部（用词必须最浅）\n\n")
        for r in rows:
            if r["book"].startswith("一年级"):
                f.write(f"- {r['ch']}（{r['py']}）：{'、'.join(r['new']) or '**无**'}\n")
        f.write("\n## 二、多音字（读音必须与本课一致）\n\n")
        for r in rows:
            if r["multi"]:
                f.write(f"- {r['ch']}（{r['py']}）[{r['book']}]："
                        f"{'、'.join(r['new']) or '**无**'}\n")
        f.write("\n## 三、取不到词\n\n")
        for r in empty:
            f.write(f"- {r['ch']}（{r['py']}）[{r['book']}]\n")
        f.write("\n## 四、拼音疑似错误（单音字与标准读音不符）\n\n")
        seen = set()
        for ch, py, only in py_bad:
            if ch in seen:
                continue
            seen.add(ch)
            f.write(f"- {ch}：数据写 {py}，标准读音 {only}\n")

        f.write("\n## 五、放宽声调取到的词（严格读音凑不满 3 个，建议人工看一眼）\n\n")
        if RELAXED_USED:
            for ch, w in sorted(RELAXED_USED):
                f.write(f"- {ch}：{w}\n")
        else:
            f.write("- 无\n")

    print(f"总条目 {len(rows)} / 改动 {changed} / 补空 {filled} / 仍空 {len(empty)}")
    print(f"拼音疑似错误 {len(set(x[0] for x in py_bad))} 字")
    print("全量报告：", REPORT)
    print("复核清单：", REVIEW)
    if not apply:
        print("\n[预览] 未写入。确认后加 --apply")


if __name__ == "__main__":
    main()
