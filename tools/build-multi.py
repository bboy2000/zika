# -*- coding: utf-8 -*-
"""
多音字重建（P2 数据层）—— 产出 mp/static/data/multi_v2.json

旧库 369 字的问题：读音靠人工列、没有出处、组词不按读音校验
（「作房」「锁哪」「鱼肚」「不更事」这类都是错读音/生僻词的残留）。

重做策略（全库 2307 字重新筛，不沿用旧名单）
1. 候选读音   pypinyin heteronym 给出该字全部读音（会带出生僻音，需筛）
2. 支撑度     ★核心★ 该读音在 jieba 34.9 万词里出现的加权词频之和
              log10(freq+1) 累加，一次性遍历该字所有词、按读音分桶
              真正常用的读音支撑度是两位数以上，生僻音接近 0
3. 读音筛选   支撑度 ≥ SUPPORT_MIN  或  是本课读音  或  有人工 override
              最多保留 MAX_READINGS 个（本课读音优先，其余按支撑度降序）
4. 组词       每个读音**独立**采词，要求同音节且同声调（多音字组词翻车的根因
              就是只校验音节），沿用 fix-words 的词频/年级/黑名单规则
5. 出处       记录该字在哪些课文出现、该课是什么读音
6. 人工表     tools/multi-override.json：{字: {tone3: [词...]}}
              进了人工表的读音完全由人工表决定，不再自动补位

用法
    python tools/build-multi.py            # 只出报告 design/multi-review.md
    python tools/build-multi.py --apply    # 写 mp/static/data/multi_v2.json
"""
import json
import math
import os
import sys
import collections

from pypinyin import pinyin as _pinyin, lazy_pinyin, Style
from pypinyin.contrib.tone_convert import to_tone, to_tone3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "fw", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix-words.py"))
fw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fw)

ROOT = fw.ROOT
SRC = fw.SRC
JIEBA = fw.JIEBA
REPORT = os.path.join(ROOT, "design", "multi-review.md")
OUT = os.path.join(ROOT, "mp", "static", "data", "multi_v2.json")
OVERRIDE_FILE = os.path.join(ROOT, "tools", "multi-override.json")

SUPPORT_MIN = 2.0        # 读音支撑度下限（生僻音基本为 0，常用音两位数）
MAX_READINGS = 3         # 单字最多展示几个读音（孩子看得过来）
WORDS_PER_READING = 3    # 每读音组词数
MULTI_MIN_FREQ = 40      # 多音字组词词频下限（比主库的 20 严得多：
                         # 「什物」89、「和弦」98 这类生僻词不能给孩子看）

# 变调不是多音字：「一」「不」的 yí/yì、bú 只是语流变调，拼音方案里本调唯一。
# 教材也从不把它们当多音字教，列三行只会让孩子混乱。
VARIANT_CHARS = {"一", "不"}

CN2NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}


def load_override():
    if not os.path.exists(OVERRIDE_FILE):
        return {}
    d = json.load(open(OVERRIDE_FILE, encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def norm_tone3(token):
    """'zhang3' / 'le' -> ('zhang', 3) / ('le', 0)"""
    if not token:
        return ("", 0)
    if token[-1].isdigit():
        return (token[:-1].lower(), int(token[-1]))
    return (token.lower(), 0)


def load_lessons():
    """字 -> [{book, name, py}]，同一字可能出现多次"""
    out = collections.defaultdict(list)
    data = json.load(open(SRC, encoding="utf-8"))
    for bid in data["order"]:
        b = data["books"][bid]
        for name, items in b["lessons"]:
            for it in items:
                out[it[0]].append({"book": b["label"], "name": name, "py": it[1]})
    return out


def split_freq(words, idx, ch, min_freq, hard_soft=False):
    """一次遍历该字所有词，按「该字在此词中读哪个音」把加权词频分桶

    返回 {tone3: 支撑度}，同时返回 {tone3: [词]} 供采词复用
    hard_soft=True 时把人名/地名/成语（SOFT_BAD_POS）也硬过滤——多音字的
    稀有读音里人名占比极高（「令 líng → 令狐冲」词频 4787 却标 nr，仅降权压不住）
    """
    buckets = collections.defaultdict(list)
    for w in idx.get(ch, []):
        if w in fw.BLACKLIST or w in fw.PLACES:
            continue
        freq, pos = words[w]
        if freq < min_freq:
            continue
        if pos in fw.HARD_BAD_POS:
            continue
        if hard_soft and pos in fw.SOFT_BAD_POS and w not in fw.ALLOW_SOFT:
            continue
        if not (2 <= len(w) <= 3):
            continue
        if any(not ("\u4e00" <= c <= "\u9fff") for c in w):
            continue
        for b, t in fw.reading_of(w, ch):
            key = f"{b}{t}" if t else b
            buckets[key].append((math.log10(freq + 1), w, pos, freq))
    return buckets


def phrase_ok(w, ch, want_t3):
    """词组库复核：库里有这个词就按库的读音判，库里没有就不表态

    pypinyin 对「大佛/成佛」标 fú、「看似」标 shì 这类错误只有词组库能兜住。
    容忍三类规范差异：变调（一/不）、轻声与本调、文白异读。
    """
    pys = fw.PHRASE_LIB.get(w)
    if not pys or len(pys) != len(w):
        return True
    got = [to_tone3(pys[i]) for i, c in enumerate(w) if c == ch]
    if not got:
        return False
    if want_t3 in got:
        return True
    want_base = want_t3.rstrip("012345")
    for g in got:
        gb = g.rstrip("012345")
        if gb == want_base and (not g[-1].isdigit() or not want_t3[-1].isdigit()):
            return True            # 轻声 / 本调之别
        if ch in fw.READING_VARIANTS and gb in fw.READING_VARIANTS[ch]:
            return True            # 文白异读
    return False


def score_words(ch, bucket, grade_of, base, tone, n):
    """按 fix-words 的打分规则从既有桶里挑词（读音已保证吻合）"""
    g0 = grade_of.get(ch, 6)
    want_t3 = f"{base}{tone}" if tone else base
    cands = []
    for base_score, w, pos, freq in bucket:
        if freq < MULTI_MIN_FREQ:      # 展示给孩子看的词要主流，词频门槛比支撑度统计高
            continue
        if not phrase_ok(w, ch, want_t3):
            continue
        score = base_score * 6.0
        if len(w) == 2:
            score += 1.2
        else:
            score -= 4.0
        over = sum(max(0, grade_of.get(c, 6) - (g0 + 1)) for c in w)
        score -= over * fw.GRADE_PENALTY
        if pos in fw.SOFT_BAD_POS and w not in fw.ALLOW_SOFT:
            score -= fw.SOFT_PENALTY
        if len(w) == 2 and w[0] == w[1]:
            score -= 0.4
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
    return out


def main():
    apply = "--apply" in sys.argv
    words = fw.load_jieba(JIEBA)
    idx = fw.build_index(words)
    grade_of = fw.load_char_grade()
    lessons = load_lessons()
    override = load_override()

    chars_out = {}
    dropped_readings = []
    no_words = []

    fw.PHRASE_LIB = fw.load_phrase()
    for ch in sorted(lessons):
        if ch in VARIANT_CHARS:
            continue
        # 该字在课文里出现过的读音（带调原文）
        lesson_pys = []
        for l in lessons[ch]:
            if l["py"] and l["py"] not in lesson_pys:
                lesson_pys.append(l["py"])
        lesson_t3 = [to_tone3(p) for p in lesson_pys]

        # pypinyin 候选读音
        r = _pinyin(ch, style=Style.TONE3, heteronym=True,
                    neutral_tone_with_five=False)
        cands = list(r[0]) if r else []

        # 一次遍历算支撑度
        # 支撑度统计用宽松门槛（fw.MIN_FREQ）：读音到底常用不常用，要看全量词
        buckets = split_freq(words, idx, ch, fw.MIN_FREQ, hard_soft=True)
        support = {k: sum(s for s, _, _, _ in v) for k, v in buckets.items()}

        # 筛选读音
        keep = []
        for t3 in cands:
            sup = support.get(t3, 0.0)
            ov = override.get(ch, {}).get(t3)
            is_lesson = t3 in lesson_t3
            if not (sup >= SUPPORT_MIN or is_lesson or ov is not None):
                if sup > 0:
                    dropped_readings.append((ch, t3, round(sup, 1)))
                continue
            keep.append((t3, sup, is_lesson))

        if len(keep) < 2:
            continue                      # 只有一个读音，不算多音字

        # 本课读音优先，其余按支撑度降序
        keep.sort(key=lambda x: (not x[2], -x[1]))
        keep = keep[:MAX_READINGS]

        readings = []
        for t3, sup, is_lesson in keep:
            ov = override.get(ch, {}).get(t3)
            if ov is not None:
                ws = [w for w in ov if ch in w and phrase_ok(w, ch, t3)]
            else:
                base, tone = norm_tone3(t3)
                ws = score_words(ch, buckets.get(t3, []), grade_of, base, tone,
                                 WORDS_PER_READING)
            if not ws:
                no_words.append((ch, t3))
                continue        # 取不到词就不展示这个读音（免得孩子点开一片空）
            readings.append({
                "py": to_tone(t3),
                "tone3": t3,
                "isLesson": is_lesson,
                "support": round(sup, 1),
                "lessons": [[l["book"], l["name"]]
                            for l in lessons[ch] if to_tone3(l["py"]) == t3],
                "words": ws,
            })

        if len(readings) < 2:
            continue            # 剔除无词组词后不足两个读音，就不算多音字
        chars_out[ch] = readings

    payload = {
        "_meta": {
            "version": "1.0",
            "generated": "2026-10-22",
            "source": "pypinyin heteronym + jieba dict 词频支撑度 + 人工表",
            "supportMin": SUPPORT_MIN,
            "maxReadings": MAX_READINGS,
            "count": len(chars_out),
        },
        "chars": chars_out,
    }

    # ---- 报告 ----
    lines = ["# 多音字重建复核（P2）", ""]
    lines.append(f"- 全库字 {len(lessons)}；筛出多音字 **{len(chars_out)}**")
    tot_r = sum(len(v) for v in chars_out.values())
    lines.append(f"- 读音条目合计 {tot_r}")
    dist = collections.Counter(len(v) for v in chars_out.values())
    lines.append(f"- 每字读音数分布：{dict(sorted(dist.items()))}")
    lines.append(f"- 支撑度不足被丢弃的读音 {len(dropped_readings)} 个")
    lines.append(f"- 取不到组词的读音 {len(no_words)} 个")
    lines.append("")
    lines.append("## 一、全量清单")
    lines.append("")
    cur = None
    for ch in sorted(chars_out):
        book = min((l["book"] for l in lessons[ch]),
                   key=lambda b: (CN2NUM.get(b[0], 6), b[2]))
        if book != cur:
            cur = book
            lines.append(f"\n### {book}\n")
        segs = []
        for rd in chars_out[ch]:
            mark = "★" if rd["isLesson"] else ""
            segs.append(f"{rd['py']}{mark}({rd['support']})：" +
                        "、".join(rd["words"]) if rd["words"] else f"{rd['py']}{mark}：——")
        lines.append(f"- **{ch}** " + " ｜ ".join(segs))
    lines.append("")
    lines.append("## 二、被丢弃的低支撑度读音")
    lines.append("")
    for ch, t3, sup in dropped_readings:
        lines.append(f"- {ch} {to_tone(t3)} {sup}")
    lines.append("")
    lines.append("## 三、取不到组词的读音")
    lines.append("")
    for ch, t3 in no_words:
        lines.append(f"- {ch} {to_tone(t3)}")
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines))

    print(f"全库字 {len(lessons)} / 多音字 {len(chars_out)} / 读音 {tot_r}")
    print(f"丢弃低支撑读音 {len(dropped_readings)} / 无组词读音 {len(no_words)}")

    if apply:
        json.dump(payload, open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        print("[写出]", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
