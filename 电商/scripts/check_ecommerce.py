# -*- coding: utf-8 -*-
"""校验 电商/ 三个词库：三字段、真 Tab、词面唯一、拼音音节数=字数、词频正整数、排序、编码。"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FILES = ["亚马逊词库.tsv", "Ozon词库.tsv", "其他词库.tsv"]

HAN = re.compile(r"^[\u3400-\u9fff]+$")
SYL = re.compile(r"^([a-z]+[1-5]|[A-Za-z0-9+\-])$")


def main():
    bad = 0
    allwords = {}
    for fn in FILES:
        path = os.path.join(REPO, "电商", fn)
        raw = io.open(path, "rb").read()
        if b"\r" in raw:
            print("%s: 含 CRLF" % fn); bad += 1
        if not raw.endswith(b"\n"):
            print("%s: 末行无换行" % fn); bad += 1
        text = raw.decode("utf-8")
        rows = []
        for ln, line in enumerate(text.splitlines(), 1):
            if line.count("\t") != 2:
                print("%s:%d 字段数不是 3: %r" % (fn, ln, line)); bad += 1
                continue
            w, py, fr = line.split("\t")
            if " " in w:
                print("%s:%d 词面含空格: %r" % (fn, ln, w)); bad += 1
            if not fr.isdigit() or int(fr) <= 0:
                print("%s:%d 词频非正整数: %r" % (fn, ln, fr)); bad += 1
            syls = py.split(" ")
            if len(syls) != len(w):
                print("%s:%d 音节数 %d != 字数 %d: %s %s"
                      % (fn, ln, len(syls), len(w), w, py)); bad += 1
            for s in syls:
                if not SYL.match(s):
                    print("%s:%d 非法音节: %r (%s)" % (fn, ln, s, w)); bad += 1
            key = w.lower()
            if key in allwords:
                print("%s:%d 词面重复（另见 %s）: %s" % (fn, ln, allwords[key], w)); bad += 1
            allwords[key] = "%s:%d" % (fn, ln)
            rows.append((w, py, int(fr)))
        if rows != sorted(rows, key=lambda r: (-r[2], r[1], r[0])):
            print("%s: 排序不符合「词频降序→拼音→词面」" % fn); bad += 1
        freq = [r[2] for r in rows]
        letters = sum(1 for r in rows if not HAN.match(r[0]))
        print("%-16s %4d 条  词频 %d—%d  含字母/数字词面 %d"
              % (fn, len(rows), min(freq), max(freq), letters))
    print("词面合计 %d，问题 %d" % (len(allwords), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
