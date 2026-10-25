# -*- coding: utf-8 -*-
"""校验合并后的 综合词库.qj。"""
import io
import pathlib
import sys

OUT = pathlib.Path(__file__).parent.parent.parent
QJ = OUT / "综合词库.qj"
BAK = OUT / ".omnicrawl/.agent_tmp/files/综合词库.qj.bak2"
SOURCES = ["英语/文学/英语文学词库.tsv", "英语/流行词/流行词汇词库.tsv"]


def load(p):
    d = {}
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[0]:
                d[parts[0]] = (parts[1], int(parts[2]))
    return d


def main():
    bad = 0
    raw = QJ.read_bytes()
    if b"\r" in raw:
        print("含 CRLF"); bad += 1
    if not raw.endswith(b"\n"):
        print("末行无换行"); bad += 1

    old = load(BAK)
    rows, preexisting = [], 0
    for ln, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if line.count("\t") != 2:
            if bad < 10:
                print("%d 字段数异常: %r" % (ln, line))
            bad += 1
            continue
        w, py, fr = line.split("\t")
        if not fr.isdigit() or int(fr) <= 0:
            print("%d 词频非法: %r" % (ln, fr)); bad += 1
        if len(py.split(" ")) != len(w):
            if old.get(w, (None,))[0] == py:
                preexisting += 1
            else:
                if bad < 20:
                    print("%d 音节数不符（本次引入）: %s %s" % (ln, w, py))
                bad += 1
        rows.append((w, py, int(fr)))

    print("行数 %d，本次引入问题 %d，既有音节例外 %d" % (len(rows), bad, preexisting))
    words = [r[0] for r in rows]
    print("词面唯一:", len(set(words)) == len(words))
    if len(set(words)) != len(words):
        bad += 1
    if rows != sorted(rows, key=lambda r: (-r[2], r[1], r[0])):
        print("排序不符合「词频降序→拼音→词面」"); bad += 1
    else:
        print("排序正确")
    print("词频区间 %d—%d" % (min(r[2] for r in rows), max(r[2] for r in rows)))

    new = {r[0]: (r[1], r[2]) for r in rows}
    lost = [w for w in old if w not in new]
    print("旧库 %d 条，丢失 %d" % (len(old), len(lost)))
    if lost:
        bad += 1
        for w in lost[:20]:
            print("  丢失:", w)

    dropped = [(w, ofr, new[w][1]) for w, (opy, ofr) in old.items() if new[w][1] < ofr]
    print("词频被降低的旧条目 %d" % len(dropped))
    for w, a, b in dropped[:20]:
        print("  %s %d→%d" % (w, a, b))
    if dropped:
        bad += 1

    added = 0
    for rel in SOURCES:
        for w in load(OUT / rel):
            if w not in old:
                added += 1
    print("预期增量 %d，实际增量 %d" % (added, len(new) - len(old)))
    if len(new) - len(old) != added:
        bad += 1

    print("结论:", "通过" if bad == 0 else "失败 %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
