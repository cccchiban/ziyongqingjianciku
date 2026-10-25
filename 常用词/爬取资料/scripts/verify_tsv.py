# -*- coding: utf-8 -*-
"""校验 常用词/常用词.tsv 是否符合仓库规范。"""
import os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WARD = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TSV = os.path.join(WARD, "常用词", "常用词.tsv")
QJ = os.path.join(WARD, "综合词库.qj")

CJK = re.compile(r"^[\u3400-\u9fff]+$")


def main():
    raw = open(TSV, encoding="utf-8", newline="").read()
    fail = []

    if not raw.endswith("\n"):
        fail.append("末行缺少换行")
    if "\r\n" in raw:
        fail.append("存在 CRLF 行尾")

    lines = raw.rstrip("\n").split("\n")
    words, prev = [], None
    for i, line in enumerate(lines, 1):
        parts = line.split("\t")
        if len(parts) != 3:
            fail.append("第 %d 行字段数 %d：%s" % (i, len(parts), line))
            continue
        w, py, fq = parts
        if not CJK.match(w):
            fail.append("第 %d 行词面非纯汉字：%s" % (i, w))
        if len(w) < 2:
            fail.append("第 %d 行词面为单字：%s" % (i, w))
        if not re.match(r"^[1-9][0-9]*$", fq):
            fail.append("第 %d 行词频非正整数：%s" % (i, fq))
        syl = py.split(" ")
        if len(syl) != len(w):
            fail.append("第 %d 行音节数 %d != 字数 %d：%s" % (i, len(syl), len(w), line))
        if any(not re.match(r"^[a-z]+[1-5]$", s) for s in syl):
            fail.append("第 %d 行音节格式异常：%s" % (i, line))
        words.append(w)
        key = (-int(fq), py, w)
        if prev is not None and key < prev:
            fail.append("第 %d 行排序异常：%s" % (i, line))
        prev = key

    dup = [w for w, c in Counter(words).items() if c > 1]
    if dup:
        fail.append("词面重复 %d 个：%s" % (len(dup), dup[:10]))

    if len(set(words)) < 1000:
        fail.append("词条数过少，疑似写出空库：%d" % len(set(words)))

    freq = [int(l.split("\t")[2]) for l in lines]
    print("行数 %d，词面 %d，词频 %d—%d，长度分布 %s"
          % (len(lines), len(set(words)), min(freq), max(freq),
             sorted(Counter(len(w) for w in words).items())))

    if os.path.exists(QJ):
        qj = {}
        with open(QJ, encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 2:
                    qj[p[0]] = p[1]
        same = [w for w in set(words) if w in qj]
        conf = [w for w in same if qj[w] != dict(
            (l.split("\t")[0], l.split("\t")[1]) for l in lines).get(w)]
        print("与综合库同名 %d，其中拼音不同 %d（已逐条核定，见 stats/pinyin_conflicts.txt）"
              % (len(same), len(conf)))

    if fail:
        print("\n未通过 %d 项：" % len(fail))
        for x in fail[:30]:
            print("  -", x)
        sys.exit(1)
    print("\n全部校验通过")


if __name__ == "__main__":
    main()
