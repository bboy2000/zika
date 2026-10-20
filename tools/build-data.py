# -*- coding: utf-8 -*-
"""
zika 小程序数据构建脚本
把 Web 版 public/chars.json 拆成小程序端可直接加载的静态数据。

输入：public/chars.json
输出：mp/static/data/
    index.json          册索引（册名/课数/字数），首页列表用
    books/<bookId>.json 单册数据（lesson -> chars）
    dict.json           全局字典（部首结构 / 释义 / 多音字）

用法：python tools/build-data.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "public", "chars.json")
OUT_DIR = os.path.join(ROOT, "mp", "static", "data")
OUT_BOOKS = os.path.join(OUT_DIR, "books")

errors = []
warns = []


def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(path)


def main():
    if not os.path.exists(SRC):
        print("源文件不存在:", SRC)
        sys.exit(1)

    with open(SRC, encoding="utf-8") as f:
        src = json.load(f)

    order = src["order"]
    labels = src["labels"]
    books = src["books"]
    radicals = src.get("radicals", {})
    explanations = src.get("explanations", {})
    multi = src.get("multi", {})

    index = {"version": src.get("version", ""), "books": []}
    all_chars = {}          # 字 -> 首次出现的 (册, 课)
    total_entries = 0

    for bid in order:
        book = books.get(bid)
        if not book:
            errors.append(f"缺少册数据: {bid}")
            continue

        lessons_out = []
        book_count = 0
        for li, lesson in enumerate(book["lessons"]):
            if not isinstance(lesson, list) or len(lesson) != 2:
                errors.append(f"{bid} 第{li+1}课结构异常")
                continue
            name, chars = lesson
            if not isinstance(chars, list) or not chars:
                errors.append(f"{bid} 《{name}》字表为空")
                continue

            chars_out = []
            for ci, item in enumerate(chars):
                if not isinstance(item, list) or len(item) < 3:
                    errors.append(f"{bid} 《{name}》第{ci+1}字结构异常: {item}")
                    continue
                ch, py, words = item[0], item[1], item[2]
                # 数据严谨性校验
                if not ch or len(ch) != 1:
                    errors.append(f"{bid} 《{name}》字非法: {ch!r}")
                if not py:
                    errors.append(f"{bid} 《{name}》{ch} 缺拼音")
                if not isinstance(words, list) or len(words) == 0:
                    warns.append(f"{bid} 《{name}》{ch} 无组词")
                elif any((not w) or (ch not in w) for w in words):
                    warns.append(f"{bid} 《{name}》{ch} 组词不含本字: {words}")

                if ch not in all_chars:
                    all_chars[ch] = (bid, name)
                chars_out.append([ch, py, words])
                book_count += 1

            lessons_out.append([name, chars_out])

        # 单册输出
        payload = {"id": bid, "label": book.get("label") or labels.get(bid, bid),
                   "lessons": lessons_out, "count": book_count}
        size = dump(payload, os.path.join(OUT_BOOKS, f"{bid}.json"))
        total_entries += book_count

        index["books"].append({
            "id": bid,
            "label": payload["label"],
            "lessonCount": len(lessons_out),
            "charCount": book_count,
            "size": size,
        })

    # 全局字典
    dict_payload = {
        "radicals": radicals,
        "explanations": explanations,
        "multi": multi,
    }
    dict_size = dump(dict_payload, os.path.join(OUT_DIR, "dict.json"))
    index_size = dump(index, os.path.join(OUT_DIR, "index.json"))

    # 多音字抽检：本课读音必须出现在该字的读音列表中
    multi_bad = []
    for ch, info in multi.items():
        base = info.get("p")
        ps = [m.get("p") for m in info.get("m", [])]
        if base and base not in ps:
            multi_bad.append(f"{ch} 本课读音 {base} 不在 {ps}")
        for m in info.get("m", []):
            for w in m.get("w", []):
                if ch not in w:
                    multi_bad.append(f"{ch} 读音{m.get('p')} 组词 {w} 不含本字")

    # 报告
    print("=" * 56)
    print(f"源文件      : {SRC}")
    print(f"总条目      : {total_entries}（源声明 {src.get('total')}）")
    print(f"唯一字      : {len(all_chars)}")
    print(f"册数        : {len(index['books'])}")
    print(f"index.json  : {index_size/1024:.1f} KB")
    print(f"dict.json   : {dict_size/1024:.1f} KB"
          f"（部首 {len(radicals)} / 释义 {len(explanations)} / 多音 {len(multi)}）")
    book_total = sum(b["size"] for b in index["books"])
    print(f"12 册合计   : {book_total/1024:.1f} KB")
    print(f"数据总计    : {(book_total+dict_size+index_size)/1024:.1f} KB")
    print()
    print("逐册：")
    for b in index["books"]:
        print(f"  {b['id']:<10} {b['label']:<8} {b['lessonCount']:>3}课 "
              f"{b['charCount']:>4}字 {b['size']/1024:>6.1f}KB")
    print()

    if errors:
        print(f"[错误] {len(errors)} 条：")
        for e in errors[:20]:
            print("  -", e)
    else:
        print("[校验] 结构错误 0")

    if multi_bad:
        print(f"[多音字] {len(multi_bad)} 条不一致：")
        for e in multi_bad[:15]:
            print("  -", e)
    else:
        print("[多音字] 读音与组词一致")

    if warns:
        print(f"[提示] {len(warns)} 条组词相关：")
        for w in warns[:15]:
            print("  -", w)
        if len(warns) > 15:
            print(f"  …… 另 {len(warns)-15} 条")
    else:
        print("[组词] 全部包含本字")


if __name__ == "__main__":
    main()
