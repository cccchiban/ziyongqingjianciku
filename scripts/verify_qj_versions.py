"""核验 综合词库 .qj/.tsv/.txt/dict.yaml 四份产物：行数、字段、排序、零丢失、零降频。"""
import hashlib
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
QJ = ROOT / "综合词库.qj"
TSV = ROOT / "综合词库.tsv"
TXT = ROOT / "综合词库.txt"
DICT = ROOT / "综合词库.dict.yaml"
BASE = ROOT / ".omnicrawl/.agent_tmp/files/综合词库.qj.pre_animals"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(p):
    d = {}
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            q = line.rstrip("\n").split("\t")
            if len(q) >= 3:
                d[q[0]] = (q[1], int(q[2]))
    return d


def main():
    err = 0
    print("md5 qj =", md5(QJ))
    for p in (TSV, TXT):
        same = md5(p) == md5(QJ)
        print("md5 %s %s" % (p.name, "一致" if same else "不一致"))
        err += 0 if same else 1

    base = load(BASE)
    cur = load(QJ)
    print("旧库 %d 条，新库 %d 条" % (len(base), len(cur)))

    lost = [w for w in base if w not in cur]
    print("旧库丢失 %d" % len(lost))
    err += 1 if lost else 0

    lowered = [(w, base[w][1], cur[w][1]) for w in base if w in cur and cur[w][1] < base[w][1]]
    print("旧词频降低 %d" % len(lowered))
    for x in lowered[:5]:
        print("   ", x)
    err += 1 if lowered else 0

    with io.open(QJ, encoding="utf-8") as f:
        lines = f.read().split("\n")
    assert lines[-1] == ""
    lines = lines[:-1]
    print("行数 %d" % len(lines))
    err += 1 if len(lines) != len(cur) else 0

    bad_field = 0
    bad_freq = 0
    bad_order = 0
    prev = None
    seen = set()
    dup = 0
    for line in lines:
        p = line.split("\t")
        if len(p) != 3:
            bad_field += 1
            continue
        w, py, fr = p
        if not fr.isdigit() or int(fr) <= 0:
            bad_freq += 1
        if w in seen:
            dup += 1
        seen.add(w)
        key = (-int(fr), py, w)
        if prev is not None and key < prev:
            bad_order += 1
        prev = key
    print("字段数异常 %d，词频异常 %d，重复词面 %d，排序错位 %d" % (bad_field, bad_freq, dup, bad_order))
    err += bad_field + bad_freq + dup + bad_order

    # dict.yaml 与 tsv 逐条对齐（编码去声调、权重=词频、顺序一致）
    with io.open(DICT, encoding="utf-8") as f:
        text = f.read().split("\n")
    idx = text.index("...")
    entries = text[idx + 1:]
    if entries and entries[-1] == "":
        entries = entries[:-1]
    print("dict.yaml 词条 %d，tsv %d" % (len(entries), len(lines)))
    mismatch = 0
    di = 0
    for i, b in enumerate(lines):
        w, py, fr = b.split("\t")
        if "/" in py or w.startswith("#"):
            continue
        code = " ".join(s.rstrip("012345") for s in py.split(" "))
        if di >= len(entries):
            mismatch += 1
            break
        a = entries[di]
        di += 1
        if a != "%s\t%s\t%s" % (w, code, fr):
            mismatch += 1
            if mismatch <= 5:
                print("   第 %d 条不符: %r vs %r" % (i + 1, a, b))
    print("dict.yaml 与 tsv 不符 %d" % mismatch)
    err += mismatch


    print("核验", "通过" if err == 0 else "失败（%d 项）" % err)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
