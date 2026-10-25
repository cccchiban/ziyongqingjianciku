"""只读预检：动漫/更新.tsv 并入 综合词库 前的影响面。"""
import io
import pathlib
import sys

REPO = pathlib.Path(__file__).parent.parent.parent.parent
QJ = REPO / "综合词库.qj"
SRC = REPO / u"动漫/更新.tsv"


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
    src = load(SRC)
    print(u"综合库原有 %d，更新.tsv %d" % (len(base), len(src)))

    new = rep = 0
    conflicts, down, up = [], [], []
    for w, (py, freq) in src.items():
        if w in base:
            rep += 1
            old_py, old_freq = base[w]
            if old_py != py:
                conflicts.append((w, old_py, py, old_freq, freq))
            if freq > old_freq:
                up.append((w, old_freq, freq))
            elif freq < old_freq:
                down.append((w, old_freq, freq))
        else:
            new += 1

    print(u"\n结论：新增 %d，已存在 %d，合并后 %d"
          % (new, rep, len(base) + new))
    print(u"已存在中：会提频 %d，会降频 %d" % (len(up), len(down)))

    if conflicts:
        print(u"\n拼音冲突 %d 条：" % len(conflicts))
        for w, opy, npy, ofr, nfr in conflicts:
            print(u"  %-22s 既有 %-30s(%4d)  本库 %-30s(%4d)"
                  % (w, opy, ofr, npy, nfr))
    else:
        print(u"拼音冲突 0 条")

    if down:
        print(u"\n!! 会降频的 %d 条（合并规则应取 max，不应出现）：" % len(down))
        for w, a, b in down[:20]:
            print(u"  %-18s %d → %d" % (w, a, b))

    if up:
        print(u"\n会提频的 %d 条（前 25）：" % len(up))
        for w, a, b in sorted(up, key=lambda x: -(x[2] - x[1]))[:25]:
            print(u"  %-22s %4d → %4d  (+%d)" % (w, a, b, b - a))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
