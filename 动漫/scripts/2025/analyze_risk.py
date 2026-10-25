"""统计 更新.tsv 里会被提频的词，区分「作品名」与「角色名」的风险规模。"""
import io
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent.parent.parent
QJ = REPO / "综合词库.qj"
SRC = REPO / u"动漫/更新.tsv"
KINDS = HERE.parent / ".omnicrawl_work" / "kinds_2025.json"


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
    kind = {r["w"]: r["kind"] for r in json.load(open(KINDS, encoding="utf-8"))}

    low2 = [w for w in src if w in base and base[w][1] < 200 and len(w) == 2
            and kind.get(w) == u"角色"]
    low_other = [w for w in src if w in base and base[w][1] < 200 and len(w) >= 3
                 and kind.get(w) == u"角色"]
    work_up = [w for w in src if w in base and base[w][1] < 200
               and kind.get(w) == u"作品"]

    print(u"已存在且旧值 <200 的词，按类型与词长分：")
    print(u"  2 字角色名 %d" % len(low2))
    print(u"  >=3 字角色名 %d" % len(low_other))
    print(u"  作品名 %d" % len(work_up))
    print(u"\n2 字角色名（全部）：")
    for w in sorted(low2):
        print(u"  %-8s 旧值 %4d → 本库 %4d" % (w, base[w][1], src[w][1]))
    print(u"\n>=3 字角色名抽样 30：")
    for w in sorted(low_other)[:30]:
        print(u"  %-12s 旧值 %4d → 本库 %4d" % (w, base[w][1], src[w][1]))

    # 全部 2 字角色名（无论是否已在库），评估丢弃损失
    all2 = [w for w in src if kind.get(w) == u"角色" and len(w) == 2]
    print(u"\n更新.tsv 中 2 字角色名共 %d，其中不在综合库 %d"
          % (len(all2), sum(1 for w in all2 if w not in base)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
