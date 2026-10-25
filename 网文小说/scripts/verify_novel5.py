# -*- coding: utf-8 -*-
"""核验五库合并后的 综合词库.qj，并同步 综合词库.tsv 副本。"""
import hashlib
import io
import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).parent.parent.parent
QJ = REPO / "综合词库.qj"
TSV = REPO / "综合词库.tsv"
BAK = REPO / ".omnicrawl/.agent_tmp/files/综合词库.qj.pre_novel5"
DAILY = REPO / "常用词/常用词.tsv"
SRCS = [REPO / ("网文小说/%s词库.tsv" % n)
        for n in (u"遮天", u"神墓", u"盘龙", u"将夜", u"仙逆")]


def load(p):
    d = {}
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[0]:
                d[parts[0]] = (parts[1], int(parts[2]))
    return d


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    bad = 0
    raw = QJ.read_bytes()
    if b"\r" in raw:
        print(u"含 CRLF")
        bad += 1
    if not raw.endswith(b"\n"):
        print(u"末行无换行")
        bad += 1

    old = load(BAK)
    src_words = set()
    for p in SRCS:
        src_words |= set(load(p))
    daily = set()
    with io.open(DAILY, encoding="utf-8") as f:
        for line in f:
            w = line.split("\t")[0].strip()
            if w:
                daily.add(w)

    rows, preexisting = [], 0
    for ln, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if line.count("\t") != 2:
            print(u"%d 字段数异常: %r" % (ln, line))
            bad += 1
            continue
        w, py, fr = line.split("\t")
        if not fr.isdigit() or int(fr) <= 0:
            print(u"%d 词频非法: %r" % (ln, fr))
            bad += 1
        if len(py.split(" ")) != len(w):
            if old.get(w, (None,))[0] == py:
                preexisting += 1
            else:
                print(u"%d 音节数不符（本次引入）: %s %s" % (ln, w, py))
                bad += 1
        rows.append((w, py, int(fr)))

    print(u"行数 %d，本次引入问题 %d，既有音节例外 %d"
          % (len(rows), bad, preexisting))

    words = [r[0] for r in rows]
    uniq = len(set(words)) == len(words)
    print(u"词面唯一: %s" % uniq)
    if not uniq:
        bad += 1
    if rows != sorted(rows, key=lambda r: (-r[2], r[1], r[0])):
        print(u"排序不符合「词频降序→拼音→词面」")
        bad += 1
    else:
        print(u"排序正确")
    print(u"词频区间 %d—%d" % (min(r[2] for r in rows), max(r[2] for r in rows)))

    new = {r[0]: (r[1], r[2]) for r in rows}
    lost = [w for w in old if w not in new]
    print(u"旧库 %d 条，丢失 %d" % (len(old), len(lost)))
    if lost:
        bad += 1
        for w in lost[:20]:
            print(u"  丢失:", w)

    dropped = [(w, ofr, new[w][1]) for w, (opy, ofr) in old.items()
               if new[w][1] < ofr]
    print(u"词频被降低的旧条目 %d" % len(dropped))
    if dropped:
        bad += 1
        for w, a, b in dropped[:20]:
            print(u"  %s %d→%d" % (w, a, b))

    expect_new = sum(1 for w in src_words if w not in old)
    actual_new = len(new) - len(old)
    print(u"预期增量 %d，实际增量 %d" % (expect_new, actual_new))
    if expect_new != actual_new:
        bad += 1

    over = [(w, old[w][1], new[w][1]) for w in src_words
            if w in old and w in daily and new[w][1] > old[w][1]]
    print(u"通用词（常用词库收录）被抬频 %d 条" % len(over))
    for w, a, b in over[:10]:
        print(u"  %s %d→%d" % (w, a, b))
    if over:
        bad += 1

    print(u"\n抽样核对（专名应提频）：")
    for w in [u"无始大帝", u"狠人大帝", u"姬紫月", u"王林", u"李慕婉",
              u"司徒南", u"林雷巴鲁克", u"宁缺", u"桑桑", u"天逆珠"]:
        o = old.get(w, (None, 0))[1]
        n = new.get(w, (None, 0))[1]
        print(u"  %-10s %4d → %4d  %s" % (w, o, n, u"✓" if n >= o else u"✗"))

    print(u"\n抽样核对（通用词应保持）：")
    for w in [u"青天", u"猫腻", u"超脱", u"天天", u"火焰", u"方块", u"玫瑰"]:
        o = old.get(w, (None, 0))[1]
        n = new.get(w, (None, 0))[1]
        print(u"  %-10s %4d → %4d  %s" % (w, o, n, u"✓" if n == o else u"✗"))

    if bad == 0:
        shutil.copy2(QJ, TSV)
        q, t = md5(QJ), md5(TSV)
        print(u"\n已同步 综合词库.tsv  md5 %s" % q)
        print(u"两者一致: %s" % (q == t))
        if q != t:
            bad += 1

    print(u"\n结论:", u"通过" if bad == 0 else u"失败 %d" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
