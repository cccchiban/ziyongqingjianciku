"""只读预检：动漫词库并入 综合词库.qj 会新增多少、覆盖多少、有无拼音冲突。"""
import io
import pathlib
import sys

OUT = pathlib.Path(__file__).parent.parent.parent
QJ = OUT / "综合词库.qj"
SRC = OUT / u"动漫/动漫词库.tsv"


def load(p):
    d = {}
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[0]:
                d[parts[0]] = (parts[1], int(parts[2]))
    return d


def main():
    base = load(QJ)
    rows = load(SRC)
    print(u"综合库原有 %d，动漫库 %d" % (len(base), len(rows)))

    new = rep = 0
    conflicts, raises = [], []
    for w, (py, freq) in rows.items():
        if w in base:
            rep += 1
            old_py, old_freq = base[w]
            if old_py != py:
                conflicts.append((w, old_py, py, old_freq, freq))
            if freq > old_freq:
                raises.append((w, old_freq, freq))
        else:
            new += 1

    print(u"新增 %d，已存在 %d，合并后 %d" % (new, rep, len(base) + new))

    print(u"\n拼音冲突 %d 条" % len(conflicts))
    for w, opy, npy, ofr, nfr in conflicts:
        print(u"  %-12s 既有 %-34s(%4d)  本库 %-34s(%4d)"
              % (w, opy, ofr, npy, nfr))

    # 提频幅度过大意味着该词在中文里是日常词，动漫义压不住，需人工判
    big = sorted([r for r in raises if r[2] - r[1] >= 200], key=lambda r: -(r[2] - r[1]))
    print(u"\n同名提频 %d 条，其中涨幅 >=200 的 %d 条" % (len(raises), len(big)))
    for w, o, n in big[:40]:
        print(u"  %-14s %4d → %4d  (+%d)" % (w, o, n, n - o))
    if len(big) > 40:
        print(u"  ... 另有 %d 条" % (len(big) - 40))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
