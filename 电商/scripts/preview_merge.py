# -*- coding: utf-8 -*-
"""只读预检：电商三库并入 综合词库.qj 会新增多少、覆盖多少、有无拼音冲突。"""
import io
import pathlib
import sys

OUT = pathlib.Path(__file__).parent.parent.parent
QJ = OUT / "综合词库.qj"

SOURCES = [
    "电商/亚马逊词库.tsv",
    "电商/Ozon词库.tsv",
    "电商/其他词库.tsv",
]


def main():
    base = {}
    with io.open(QJ, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                base[p[0]] = (p[1], int(p[2]))
    print("综合库原有", len(base))

    total_new = 0
    conflicts = []
    for rel in SOURCES:
        rows = []
        with io.open(OUT / rel, encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 3 and p[0]:
                    rows.append((p[0], p[1], int(p[2])))
        new = rep = 0
        for w, py, freq in rows:
            if w in base:
                rep += 1
                old_py, old_freq = base[w]
                if old_py != py:
                    conflicts.append((w, old_py, py, old_freq, freq))
            else:
                new += 1
        total_new += new
        print("%-22s %5d 条  新增 %5d  已存在 %4d"
              % (rel.split("/")[-1], len(rows), new, rep))

    print("新增合计", total_new, "合并后", len(base) + total_new)
    if conflicts:
        print("拼音冲突 %d 条（合并后按本库拼音覆盖）：" % len(conflicts))
        for w, opy, npy, ofr, nfr in conflicts:
            print("  %-12s 既有 %-28s(%d)  本库 %-28s(%d)" % (w, opy, ofr, npy, nfr))
    else:
        print("拼音冲突 0 条")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
