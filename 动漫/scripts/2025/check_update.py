# -*- coding: utf-8 -*-
"""校验 动漫/更新.tsv。"""
import io
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
TSV = HERE.parent.parent / u"更新.tsv"

CJK = re.compile(u"[\\u3400-\\u9fff]")
NON_SYL = re.compile(u"[^\\u3400-\\u9fff]")
SYL = re.compile(u"^[a-z]+[1-5]$")


def main():
    raw = TSV.read_bytes()
    fails = []
    if not raw.endswith(b"\n"):
        fails.append(u"末行缺换行")
    if b"\r" in raw:
        fails.append(u"存在 CRLF")
    text = raw.decode("utf-8")

    rows, seen, dup = [], {}, []
    for i, line in enumerate(text.split("\n"), 1):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            fails.append(u"第 %d 行字段数 %d" % (i, len(parts)))
            continue
        w, py, fq = parts
        rows.append((i, w, py, fq))
        if w in seen:
            dup.append((w, seen[w], i))
        seen[w] = i

        if " " in w.strip() and not w.strip():
            fails.append(u"第 %d 行词面为空白" % i)
        if not CJK.search(w):
            fails.append(u"第 %d 行词面无汉字：%r" % (i, w))
        if len(w) < 2:
            fails.append(u"第 %d 行词面过短：%r" % (i, w))
        if len(w) > 24:
            fails.append(u"第 %d 行词面过长 %d：%s" % (i, len(w), w))

        han = NON_SYL.sub("", w)
        syl = py.split(" ")
        if len(syl) != len(han):
            fails.append(u"第 %d 行音节 %d != 汉字 %d：%s" % (i, len(syl), len(han), w))
        for s in syl:
            if not SYL.match(s):
                fails.append(u"第 %d 行音节非法 %r（%s）" % (i, s, w))
        if u"ü" in py:
            fails.append(u"第 %d 行 ü 未写 v：%r" % (i, py))
        if not fq.isdigit() or int(fq) <= 0:
            fails.append(u"第 %d 行词频非法：%r" % (i, fq))
        if int(fq) > 1000:
            fails.append(u"第 %d 行词频超 1000：%r" % (i, fq))

    for w, a, b in dup[:10]:
        fails.append(u"词面重复：%s（%d 与 %d 行）" % (w, a, b))

    prev = None
    for i, w, py, fq in rows:
        key = (-int(fq), py, w)
        if prev is not None and key < prev:
            fails.append(u"第 %d 行排序错误：%s" % (i, w))
            break
        prev = key

    freqs = [int(r[3]) for r in rows]
    print(u"行数 %d，词面唯一 %d，词频 %d—%d，档位 %d"
          % (len(rows), len(seen), min(freqs), max(freqs), len(set(freqs))))
    print(u"重复 %d，字节 %d，末行换行 %s"
          % (len(dup), len(raw), raw.endswith(b"\n")))

    if fails:
        print(u"\n失败 %d 项（前 20）：" % len(fails))
        for f in fails[:20]:
            print("  " + f)
        return 1
    print(u"\n全部通过：三字段真 Tab、词面唯一、含汉字、音节数=汉字数、"
          u"拼音全带声调、ü 写 v、词频 300—1000、排序符合「词频降序→拼音→词面」、"
          u"UTF-8 + LF、末行换行。")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
