"""核验 更新.tsv 并入后的 综合词库.qj 与 综合词库.tsv。"""
import io
import hashlib
import pathlib
import sys

REPO = pathlib.Path(__file__).parent.parent.parent.parent
QJ = REPO / "综合词库.qj"
TSV = REPO / "综合词库.tsv"
BAK = REPO / ".omnicrawl/.agent_tmp/files/综合词库.qj.bak4"
SRC = REPO / u"动漫/更新.tsv"
DAILY_FLOOR = 200


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

    a, b = md5(QJ), md5(TSV)
    print(u"qj  md5 %s" % a)
    print(u"tsv md5 %s  %s" % (b, u"一致" if a == b else u"!! 不一致"))
    if a != b:
        bad += 1

    old = load(BAK)
    src = load(SRC)
    rows = []
    for ln, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if line.count("\t") != 2:
            if bad < 10:
                print(u"%d 字段数异常: %r" % (ln, line))
            bad += 1
            continue
        w, py, fr = line.split("\t")
        if not fr.isdigit() or int(fr) <= 0:
            print(u"%d 词频非法: %r" % (ln, fr))
            bad += 1
        rows.append((w, py, int(fr)))

    print(u"\n行数 %d" % len(rows))
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
    print(u"\n旧库 %d 条，丢失 %d" % (len(old), len(lost)))
    if lost:
        bad += 1
        for w in lost[:20]:
            print(u"  丢失:", w)

    dropped = [(w, ofr, new[w][1]) for w, (opy, ofr) in old.items()
               if new[w][1] < ofr]
    print(u"词频被降低的旧条目 %d" % len(dropped))
    for w, x, y in dropped[:20]:
        print(u"  %s %d→%d" % (w, x, y))
    if dropped:
        bad += 1

    expect_new = sum(1 for w in src if w not in old)
    actual_new = len(new) - len(old)
    print(u"预期增量 %d，实际增量 %d" % (expect_new, actual_new))
    if expect_new != actual_new:
        bad += 1

    over = [(w, old[w][1], new[w][1]) for w in src
            if w in old and old[w][1] >= DAILY_FLOOR and new[w][1] > old[w][1]]
    print(u"通用词（旧>=%d）被抬频的 %d 条" % (DAILY_FLOOR, len(over)))
    for w, x, y in over[:15]:
        print(u"  %s %d→%d" % (w, x, y))
    if over:
        bad += 1

    print(u"\n抽样核对：")
    for w in [u"青菜", u"老鸨", u"乔琳", u"全力兔", u"杜鹃婚约",
              u"胆大党", u"坂本日常", u"拿破仑"]:
        o = old.get(w, (None, 0))[1]
        n = new.get(w, (None, 0))[1]
        print(u"  %-10s %4d → %4d" % (w, o, n))

    print(u"\n结论:", u"通过" if bad == 0 else u"失败 %d" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
