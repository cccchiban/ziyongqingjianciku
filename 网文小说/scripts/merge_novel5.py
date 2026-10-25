# -*- coding: utf-8 -*-
"""把 网文小说/ 下遮天、神墓、盘龙、将夜、仙逆 五库并入 综合词库.qj。

合并规则：
- 词面已存在：拼音取本库值，词频取 max(旧值, 本库值)。
- 词面不存在：直接加入。
- 通用词不抬频：判据用 常用词/常用词.tsv（543.7 万条真实评论统计出的
  口语高频词）是否为该词收录，而不是综合库的旧词频阈值。

  旧写法 DAILY_FLOOR=200 是错的：2026-10-25 动漫库合并时 `天天` 旧值仅 60、
  仍被抬到 800，阈值根本没拦住；而本次 `无始大帝`「姬紫月」旧值 203 却被
  误判为通用词。203 不是通用性指标，是 `文学作品/文学作品词库.tsv` 导入
  综合库时的统一降频值（文学库 560 → 综合库 203），1719 个词共用该值，
  下面是 `煤油`「程序化」这类日常词，上面是 `荒古圣体`「帝尊」这类专名。
  用 常用词.tsv 判：`无始大帝`「王林」「李慕婉」「荒古圣体」全部不在其中，
  `天天`「火焰」「方块」「玫瑰」全部在，两类干净分开。

--preview 只算不写。
"""
import io
import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).parent.parent.parent
QJ = REPO / "综合词库.qj"
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


def load_words(p):
    s = set()
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            w = line.split("\t")[0].strip()
            if w:
                s.add(w)
    return s


def main():
    preview = "--preview" in sys.argv
    base = load(QJ)
    daily = load_words(DAILY)
    print(u"合并前 %d 条，常用词判据 %d 条" % (len(base), len(daily)))

    new = raised = hold = 0
    held_rows = []
    for src_path in SRCS:
        src = load(src_path)
        s_new = s_raised = s_hold = 0
        for w, (py, freq) in src.items():
            if w in daily:
                s_hold += 1
                held_rows.append((w, base.get(w, (None, 0))[1], freq))
                if w in base:
                    base[w] = (py, base[w][1])
                else:
                    base[w] = (py, freq)
                continue
            if w in base:
                old_freq = base[w][1]
                if freq > old_freq:
                    s_raised += 1
                base[w] = (py, max(old_freq, freq))
            else:
                s_new += 1
                base[w] = (py, freq)
        print(u"  %-8s 新增 %3d 提频 %3d 通用词保持 %2d"
              % (src_path.stem, s_new, s_raised, s_hold))
        new += s_new
        raised += s_raised
        hold += s_hold

    rows = sorted(((w, py, f) for w, (py, f) in base.items()),
                  key=lambda r: (-r[2], r[1], r[0]))
    print(u"合计 新增 %d，提频 %d，通用词保持 %d，合并后 %d"
          % (new, raised, hold, len(rows)))
    if held_rows:
        print(u"通用词保持原值: %s"
              % u", ".join(u"%s(%d>%d)" % h for h in held_rows[:15]))

    if preview:
        print(u"[预览] 未写盘")
        return 0
    if len(rows) < len(base) * 0.99:
        print(u"行数异常，拒绝写盘")
        return 1

    if not BAK.exists():
        shutil.copy2(QJ, BAK)
        print(u"已备份至 %s" % BAK.relative_to(REPO))

    with io.open(QJ, "w", encoding="utf-8", newline="\n") as f:
        for w, py, fr in rows:
            f.write(u"%s\t%s\t%d\n" % (w, py, fr))
    print(u"已写入 %s" % QJ.name)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
