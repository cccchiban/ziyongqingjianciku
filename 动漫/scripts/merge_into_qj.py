"""把 动漫/动漫词库.tsv 并入 综合词库.qj。

合并规则（与仓库既有合并脚本一致）：
- 词面已存在：拼音取本库值，词频取 max(旧值, 本库值)。
- 词面不存在：直接加入。
- 例外：旧词频 >= DAILY_FLOOR 的通用词不抬频。动漫库里 `天天`(10 库)、
  `方块`(12 库) 这类既被动漫库收录、又是成熟中文通用词的，动漫义压不住日常义，
  抬频会挤掉日常候选。判据只能用综合库既有词频——共现数无法区分：`天天` 10 库
  与 `漩涡鸣人` 12 库同量级。
"""
import io
import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).parent.parent.parent
QJ = REPO / "综合词库.qj"
BAK = REPO / ".omnicrawl/.agent_tmp/files/综合词库.qj.bak3"
SRC = REPO / u"动漫/动漫词库.tsv"
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
    hold = 0
    new = raised = 0
    for w, (py, freq) in src.items():
        if w in base:
            old_freq = base[w][1]
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
    with io.open(QJ, "w", encoding="utf-8", newline="\n") as f:
        for w, py, fr in rows:
            f.write(u"%s\t%s\t%d\n" % (w, py, fr))
    print(u"新增 %d，提频 %d，通用词保持原值 %d，合并后 %d"
          % (new, raised, hold, len(rows)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
