"""把 动漫/更新.tsv 并入 综合词库.qj 与 综合词库.tsv。

合并规则（与 `动漫/scripts/merge_into_qj.py` 一致）：
- 词面已存在：拼音取本库值（拼音冲突预检为 0），词频取 max(旧值, 本库值)。
- 词面不存在：直接加入。
- 例外：旧词频 >= DAILY_FLOOR 的通用词只更新拼音、保持词频。`索菲亚` 203、
  `拿破仑` 224、`印第安` 等已是综合库按通用词确立的，动漫义压不住日常义。

两个目标文件都要写：`综合词库.tsv` 是 `综合词库.qj` 的逐字节副本，合并后
必须重新同步，否则两者内容会分叉。
"""
import io
import pathlib
import shutil
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


def main():
    if not BAK.exists():
        shutil.copy2(QJ, BAK)
        print(u"已备份至 %s" % BAK.relative_to(REPO))

    base = load(QJ)
    src = load(SRC)
    hold = new = raised = 0
    for w, (py, freq) in src.items():
        if w in base:
            old_py, old_freq = base[w]
            if old_freq >= DAILY_FLOOR:
                hold += 1
                base[w] = (py, old_freq)
                continue
            if freq > old_freq:
                raised += 1
            base[w] = (py, max(old_freq, freq))
        else:
            new += 1
            base[w] = (py, freq)

    rows = sorted(((w, py, f) for w, (py, f) in base.items()),
                  key=lambda r: (-r[2], r[1], r[0]))
    body = u"\n".join(u"%s\t%s\t%d" % r for r in rows) + u"\n"
    with io.open(QJ, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print(u"新增 %d，提频 %d，通用词保持原值 %d，合并后 %d"
          % (new, raised, hold, len(rows)))

    # 副本逐字节同步
    shutil.copyfile(QJ, TSV)
    print(u"已同步 %s" % TSV.name)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
