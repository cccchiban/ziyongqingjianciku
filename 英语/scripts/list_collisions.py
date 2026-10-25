# -*- coding: utf-8 -*-
"""导出 英语两库 与 综合词库.qj 的同名词面清单，供人工审查是否为日常通用词。"""
import io
import pathlib
import sys

OUT = pathlib.Path(__file__).parent.parent.parent
QJ = OUT / "综合词库.qj"
SOURCES = ["英语/文学/英语文学词库.tsv", "英语/流行词/流行词汇词库.tsv"]


def main():
    base = {}
    with io.open(QJ, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                base[p[0]] = (p[1], int(p[2]))

    for rel in SOURCES:
        print("=== %s ===" % rel)
        n = 0
        with io.open(OUT / rel, encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) < 3:
                    continue
                w, py, fr = p[0], p[1], int(p[2])
                if w in base:
                    n += 1
                    print("%-22s 综合库 %5d  本库 %4d" % (w, base[w][1], fr))
        print("小计 %d 条\n" % n)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
