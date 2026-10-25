# -*- coding: utf-8 -*-
"""校验 英语/流行词/流行词汇词库.tsv。

重点：词面必须是纯拉丁字母数字（可含数字）、拼音字段逐字符分隔、
不含空格、词频正整数、排序符合「词频降序→拼音→词面」。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TARGET = os.path.join(REPO, "英语", "流行词", "流行词汇词库.tsv")

TOKEN = re.compile(r"^[A-Za-z0-9]+$")


def main():
    bad = 0
    raw = io.open(TARGET, "rb").read()
    if b"\r" in raw:
        print("含 CRLF"); bad += 1
    if not raw.endswith(b"\n"):
        print("末行无换行"); bad += 1

    rows, seen = [], {}
    for ln, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if line.count("\t") != 2:
            print("%d 字段数不是 3: %r" % (ln, line)); bad += 1; continue
        w, py, fr = line.split("\t")
        if not TOKEN.match(w):
            print("%d 词面不是纯拉丁字母数字: %r" % (ln, w)); bad += 1
        if " " in w or "\t" in w:
            print("%d 词面含空白: %r" % (ln, w)); bad += 1
        if not fr.isdigit() or int(fr) <= 0:
            print("%d 词频非正整数: %r" % (ln, fr)); bad += 1
        syls = py.split(" ")
        if len(syls) != len(w):
            print("%d 音节数 %d != 字数 %d: %s %s"
                  % (ln, len(syls), len(w), w, py)); bad += 1
        if " ".join(w) != py:
            print("%d 拼音不是逐字符分隔: %s %s" % (ln, w, py)); bad += 1
        if w.lower() in seen:
            print("%d 词面重复（另见 %d）: %s" % (ln, seen[w.lower()], w)); bad += 1
        seen[w.lower()] = ln
        rows.append((w, py, int(fr)))

    if rows != sorted(rows, key=lambda r: (-r[2], r[1], r[0])):
        print("排序不符合「词频降序→拼音→词面」"); bad += 1

    freq = [r[2] for r in rows]
    print("%d 条，词频 %d—%d，最短 %d 字符，最长 %d 字符"
          % (len(rows), min(freq), max(freq),
             min(len(r[0]) for r in rows), max(len(r[0]) for r in rows)))
    print("结论:", "通过" if bad == 0 else "失败 %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
