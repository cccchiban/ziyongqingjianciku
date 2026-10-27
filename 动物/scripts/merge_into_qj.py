"""把动物词表并入 综合词库.qj，并同步 .tsv / .txt 副本。

规则：词面去重；核心读音以动物名录为准；词频取最大，但俗名不得抬升既有词条
（俗名与日常词大量同形，抬频会挤掉日常候选）。
"""
import io
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORDLIST = ROOT / ".omnicrawl/.agent_tmp/files/animal_wordlist.tsv"
QJ = ROOT / "综合词库.qj"
COPIES = [ROOT / "综合词库.tsv", ROOT / "综合词库.txt"]

PINYIN_FIX = {
    "藏狐": "zang4 hu2",
    "长尾鼠耳蝠": "chang2 wei3 shu3 er3 fu2",
}


def load_rows():
    rows = []
    with io.open(WORDLIST, encoding="utf-8") as f:
        for line in f:
            w, py, kind, freq = line.rstrip("\n").split("\t")
            rows.append((w, py, kind, int(freq)))
    return rows


def main(preview=False):
    rows = load_rows()
    base = {}
    with io.open(QJ, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                base[p[0]] = (p[1], int(p[2]))
    before = len(base)
    print("综合库原有", before)

    added = alias_added = raised = unchanged = 0
    conflicts = []
    for w, py, kind, freq in rows:
        if w in base:
            opy, ofreq = base[w]
            newpy = PINYIN_FIX.get(w, py)
            if kind == "alias":
                freq = ofreq          # 俗名不改既有词频
            nfreq = max(ofreq, freq)
            if nfreq > ofreq:
                raised += 1
            else:
                unchanged += 1
            if newpy != opy:
                conflicts.append((w, opy, newpy))
            base[w] = (newpy, nfreq)
        else:
            base[w] = (PINYIN_FIX.get(w, py), freq)
            added += 1
            if kind == "alias":
                alias_added += 1

    print("新增 %d（其中俗名 %d），提频 %d，保持原值 %d" % (added, alias_added, raised, unchanged))
    print("读音变更 %d" % len(conflicts))
    for c in sorted(conflicts):
        print("   %-12s %s -> %s" % c)
    print("合并后", len(base), "预期增量", added)
    assert len(base) == before + added

    if preview:
        print("预检模式，未写盘")
        return

    lines = ["%s\t%s\t%d" % (w, py, freq) for w, (py, freq) in base.items()]
    lines.sort(key=lambda s: (lambda p: (-int(p[2]), p[1], p[0]))(s.split("\t")))
    with io.open(QJ, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    for c in COPIES:
        shutil.copyfile(QJ, c)
    print("写出 %s 及 %d 份副本，共 %d 条" % (QJ.name, len(COPIES), len(lines)))


if __name__ == "__main__":
    main(preview="--preview" in sys.argv)
