"""把四个专业库并入 综合词库.qj：词面去重、词频取最大、源库拼音优先、词频降序→拼音→词面。"""
import io
import pathlib
import sys

OUT = pathlib.Path(__file__).parent.parent
QJ = OUT / "综合词库.qj"

SOURCES = [
    "计算机词库/计算机词库.tsv",
    "电力电气/电力电气词库.tsv",
    "通信与无线电/通信与无线电词库.tsv",
    "电子工程/电子工程词库.tsv",
]


def main():
    base = {}
    with io.open(QJ, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                base[p[0]] = (p[1], int(p[2]))
    print("综合库原有", len(base))

    added = replaced = 0
    for rel in SOURCES:
        rows = []
        with io.open(OUT / rel, encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 3 and p[0]:
                    rows.append((p[0], p[1], int(p[2])))
        new = 0
        for w, py, freq in rows:
            if w in base:
                opy, ofreq = base[w]
                base[w] = (py, max(ofreq, freq))   # 源库拼音优先，词频取最大
                replaced += 1
            else:
                base[w] = (py, freq)
                new += 1
        added += new
        print("%-30s %6d 条，新增 %6d" % (rel.split("/")[-1], len(rows), new))

    print("新增合计", added, "已存在覆盖", replaced, "合并后", len(base))
    assert len(base) > 1025757, "合并后未增加，拒绝写出"

    lines = ["%s\t%s\t%d" % (w, py, freq) for w, (py, freq) in base.items()]
    lines.sort(key=lambda s: (lambda p: (-int(p[2]), p[1], p[0]))(s.split("\t")))
    with io.open(QJ, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("写出", QJ.name, len(lines), "条")


if __name__ == "__main__":
    main()
