"""植物词表定词频。

语料库（常用词/常用词.tsv）里有的直接采用 df；其余按长度分档，
单字正名略高。区间压在 700 以下——植物名录是冷僻种占多数的长名词表，
抬到 800 档会挤掉日常候选。

并入综合库时另做降档：本表是独立库的相对档位，直接并进 160 万条的综合库
会让 83137 条净新增全部落在 600 档以上，见 merge_into_qj.py。
"""
import io
import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENTRIES = HERE / "data" / "plant_entries.tsv"
OUT = HERE / "data" / "plant_wordlist.tsv"
LIB = HERE.parent / "植物词库.tsv"
COMMON = ROOT / "常用词" / "常用词.tsv"

# 单字植物名：保留日常会单独敲的（树名、作物、蔬菜、药草）
COMMON_SINGLE = set(
    "松柏杉柳杨槐榆桐桃杏李梅梨枣柿橘橙柚竹莲荷菊兰麻稻麦粟粱稷"
    "芋茄葱蒜韭姜芥苋艾茶桑漆樟栾樟榛栗榧桉梓楝楸榆柚莼菰荠蓟蓍藜荻蒲"
)

LADDER = {2: 690, 3: 668, 4: 648, 5: 628, 6: 612}
SINGLE = 700


def load_common():
    d = {}
    with io.open(COMMON, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                d[p[0]] = int(p[2])
    return d


def main():
    common = load_common()
    rows = []
    with io.open(ENTRIES, encoding="utf-8") as f:
        for line in f:
            w, py, kind, _ = line.rstrip("\n").split("\t")
            rows.append((w, py, kind))

    out, dropped = [], []
    for w, py, kind in rows:
        if len(w) == 1:
            if w not in COMMON_SINGLE:
                dropped.append((w, "冷僻单字"))
                continue
            freq = SINGLE
        elif w in common:
            freq = common[w]
        else:
            freq = LADDER.get(len(w), 600)
        out.append((w, py, kind, freq))

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for w, py, kind, freq in sorted(out):
            f.write("%s\t%s\t%s\t%d\n" % (w, py, kind, freq))
    st = {}
    for _, why in dropped:
        st[why] = st.get(why, 0) + 1
    print("词表 %d 条，剔除 %d 条 %s" % (len(out), len(dropped), st))
    print("词频区间 %d—%d" % (min(r[3] for r in out), max(r[3] for r in out)))


if __name__ == "__main__":
    main()
