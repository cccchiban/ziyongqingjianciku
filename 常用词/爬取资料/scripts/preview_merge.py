# -*- coding: utf-8 -*-
"""预览把 常用词/常用词.tsv 并入 综合词库.qj 的影响，不写任何文件。"""
import io
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
QJ = ROOT / "综合词库.qj"
SRC = ROOT / "常用词" / "常用词.tsv"


def load(path):
    d = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                d[p[0]] = (p[1], int(p[2]))
    return d


def main():
    base = load(QJ)
    src = load(SRC)
    print("综合库 %d 条，常用词 %d 条" % (len(base), len(src)))

    dup_src = []
    with io.open(SRC, encoding="utf-8") as f:
        words = [l.split("\t")[0] for l in f if l.strip()]
    c = Counter(words)
    dup_src = [(w, n) for w, n in c.items() if n > 1]
    print("常用词内部重复词面：%d" % len(dup_src))

    new, exist = [], []
    for w, (py, fq) in src.items():
        if w in base:
            exist.append((w, base[w][1], fq, base[w][0], py))
        else:
            new.append((w, py, fq))

    print("新增 %d 条，已存在 %d 条" % (len(new), len(exist)))

    py_conf = [e for e in exist if e[3] != e[4]]
    print("拼音冲突 %d 条" % len(py_conf))

    up = [e for e in exist if e[2] > e[1]]
    same = [e for e in exist if e[2] == e[1]]
    down = [e for e in exist if e[2] < e[1]]
    print("已存在中：提频 %d、持平 %d、新库更低 %d（按 max 规则不会降频）"
          % (len(up), len(same), len(down)))

    big = sorted(up, key=lambda e: -(e[2] - e[1]))[:25]
    print("\n提频幅度最大的 25 条（旧→新）：")
    for w, old, newf, opy, npy in big:
        print("   %-10s %5d → %-5d  +%d" % (w, old, newf, newf - old))

    # 抬到 800 档以上的词，逐个看它原来的归属档位
    hi = [e for e in up if e[2] >= 800]
    print("\n被抬到 800 档以上的 %d 条，原词频分布 %s"
          % (len(hi), sorted(Counter(
              "0-100" if e[1] < 100 else "100-300" if e[1] < 300
              else "300-600" if e[1] < 600 else "600+" for e in hi).items())))

    print("\n新增词条前 20：")
    for w, py, fq in sorted(new, key=lambda x: -x[2])[:20]:
        print("   %-10s %-24s %d" % (w, py, fq))

    if py_conf:
        print("\n拼音冲突全部（旧 → 新）：")
        for w, old, newf, opy, npy in sorted(py_conf):
            print("   %-10s %-22s → %s" % (w, opy, npy))

    assert len(new) + len(exist) == len(src)
    print("\n合并后预计 %d 条（净增 %d）" % (len(base) + len(new), len(new)))


if __name__ == "__main__":
    main()
