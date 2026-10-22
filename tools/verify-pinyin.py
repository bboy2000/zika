# -*- coding: utf-8 -*-
"""
读音双源校验（P2）—— 挑出组词读音拿错的词

为什么需要：jieba 只给词频、不给读音，fix-words 用的是 pypinyin 反查读音。
pypinyin 内置词组词典很小，对「大佛」标 fú、「看似」标 shì、「登场」标 cháng
这类错误无能为力，会把错读音的词放进数据。

双源
1. phrase-pinyin-data（mozillazg，4.7 万词组带拼音）—— 词组级，最权威
   https://github.com/mozillazg/phrase-pinyin-data
2. pinyin-data（同作者，4.4 万单字全读音）—— 单字级，只用来判断
   「这个读音是不是该字的合法读音」，不用来判断哪个音更常用
   https://github.com/mozillazg/pinyin-data

判定
- 词组库命中且读音一致        OK
- 词组库命中但读音不一致       BAD（拿错读音，必须修）
- 词组库未收录，读音合法        UNKNOWN（pypinyin 与单字表都支持，可信度中）
- 词组库未收录，读音不合法      ILLEGAL（该字根本没这个读音，必错）

用法
    python tools/verify-pinyin.py                # 校验主库组词
    python tools/verify-pinyin.py --multi        # 连多音字表一起校验
"""
import json
import os
import sys
import collections
import glob

from pypinyin import lazy_pinyin, Style
from pypinyin.contrib.tone_convert import to_tone3, to_tone as tone3_to_tone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHRASE = os.path.join(ROOT, "tools", "phrase-pinyin.txt")
CHARDATA = os.path.join(ROOT, "tools", "pinyin-data.txt")
REPORT = os.path.join(ROOT, "design", "pinyin-verify.md")

# 与 fix-words 保持同一套放宽规则，否则报告里会堆满「假阳性」
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "fw", os.path.join(ROOT, "tools", "fix-words.py"))
fw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fw)


def load_phrase():
    lib = {}
    for line in open(PHRASE, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        w, p = line.split(":", 1)
        lib[w.strip()] = p.split()
    return lib


def load_char_readings():
    """字 -> 该字的全部合法读音（带调，不含声调数字）"""
    out = {}
    for line in open(CHARDATA, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("U+"):
            continue
        head, _, _ = line.partition("#")
        if ":" not in head:
            continue
        code, pys = head.split(":", 1)
        try:
            ch = chr(int(code[2:], 16))
        except ValueError:
            continue
        out[ch] = [p.strip() for p in pys.split(",") if p.strip()]
    return out


def strip_tone(py):
    """带调拼音 -> tone3 形式（zhǎng -> zhang3 / le -> le）"""
    return to_tone3(py)


def check_word(w, ch, want_tone3, phrase, charlib):
    """返回 (状态, 实际读音)"""
    if w in phrase:
        pys = phrase[w]
        if len(pys) != len(w):
            return ("BADLEN", " ".join(pys))
        for i, c in enumerate(w):
            if c != ch:
                continue
            got = strip_tone(pys[i])
            if got == want_tone3:
                return ("OK", pys[i])
            # 以下三类是规范允许的差异，不算错：
            # 1) 一/不 的变调（一个 yí、不是 bú）
            if ch in fw.SANDBOX_CHARS:
                return ("OK*", pys[i])
            want_base = want_tone3.rstrip("012345")
            got_base = got.rstrip("012345")
            # 2) 轻声与本调之别：同音节，一个带调一个不带
            #    （词典 儿子 zi / 课本 zǐ；词典 胳膊 bó / 课本 bo）
            if got_base == want_base and (not got[-1].isdigit()
                                          or not want_tone3[-1].isdigit()):
                return ("OK*", pys[i])
            # 3) 文白异读（谁 shuí/shéi、那 nà/nèi）
            if ch in fw.READING_VARIANTS and got_base in fw.READING_VARIANTS[ch]:
                return ("OK*", pys[i])
            return ("BAD", pys[i])
        return ("NOTFOUND", "")
    # 库未收录：只能判断「读音合法不合法」
    want = want_tone3
    legal = charlib.get(ch, [])
    if not legal:
        return ("UNKNOWN", "")
    legal_t3 = {strip_tone(p) for p in legal}
    if want in legal_t3:
        return ("UNKNOWN", "")
    return ("ILLEGAL", "/".join(legal))


def main():
    with_multi = "--multi" in sys.argv
    phrase = load_phrase()
    charlib = load_char_readings()
    charlib = {k: v for k, v in charlib.items() if len(k) == 1}

    items = []      # (来源, 字, 本课拼音, 词)
    data = json.load(open(os.path.join(ROOT, "public", "chars.json"), encoding="utf-8"))
    for bid in data["order"]:
        b = data["books"][bid]
        for name, lesson in b["lessons"]:
            for it in lesson:
                ch, py, ws = it[0], it[1], it[2] or []
                for w in ws:
                    items.append((f"{b['label']}/{name}", ch, py, w))

    if with_multi:
        mp = os.path.join(ROOT, "mp", "static", "data", "multi_v2.json")
        if os.path.exists(mp):
            md = json.load(open(mp, encoding="utf-8"))["chars"]
            for ch, readings in md.items():
                for rd in readings:
                    t3 = rd["tone3"]
                    for w in rd["words"]:
                        items.append((f"多音字/{rd['py']}", ch, tone3_to_tone(t3), w))

    stat = collections.Counter()
    bad, illegal = [], []
    for src, ch, py, w in items:
        want = to_tone3(py)
        st, got = check_word(w, ch, want, phrase, charlib)
        stat[st] += 1
        if st == "BAD":
            bad.append((ch, py, w, got, src))
        elif st == "ILLEGAL":
            illegal.append((ch, py, w, got, src))

    lines = ["# 组词读音双源校验（P2）", ""]
    lines.append(f"- 词组库 {len(phrase)} 条 / 单字表 {len(charlib)} 字")
    lines.append(f"- 校验组词 **{len(items)}** 条" + ("（含多音字表）" if with_multi else ""))
    for k in ("OK", "OK*", "UNKNOWN", "BAD", "ILLEGAL", "BADLEN", "NOTFOUND"):
        if stat[k]:
            lines.append(f"- {k}: {stat[k]}")
    lines.append("（OK* = 变调 / 连读轻声 / 文白异读，规范允许，不算错）")
    lines.append("")
    lines.append("## 一、读音拿错（词组库明确给出不同读音）")
    lines.append("")
    for ch, py, w, got, src in bad:
        lines.append(f"- **{ch}** {w}：数据按 {py}，词典读 {got} —— {src}")
    lines.append("")
    lines.append("## 二、读音不合法（该字没有这个读音）")
    lines.append("")
    for ch, py, w, got, src in illegal:
        lines.append(f"- **{ch}** {w}：数据按 {py}，该字合法读音 {got} —— {src}")
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines))

    print(f"校验 {len(items)} 条：OK {stat['OK']} / OK*(变调轻声文白) {stat['OK*']} "
          f"/ UNKNOWN {stat['UNKNOWN']} "
          f"/ BAD {stat['BAD']} / ILLEGAL {stat['ILLEGAL']}")
    print(f"报告 {REPORT}")


if __name__ == "__main__":
    main()
