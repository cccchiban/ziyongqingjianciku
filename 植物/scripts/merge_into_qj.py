"""把植物词表并入 综合词库.qj，并同步 .tsv / .txt 副本。

三步：
1. 词频重定档。植物词库的 600—700 是独立库里的相对档位，83137 条净新增
   直接沿用会让综合库 >=600 档从 435394 涨到 518531，故改用长度档
   （2 字 380 → 12 字 296）。语料里查得到 df 的按 df 折算，它们才是真在用的。
2. 同码保护。去声调后编码相同的既有日常词（常用词/常用词.tsv 白名单）不许被
   新增词压过，否则 `硕桦` 会排在 `说话` 前面。触发时压到对手之下。
3. 合并。正名参与提频，俗名只新增——俗名与日常词大量同形。
"""
import csv
import io
import math
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORDLIST = HERE / "data" / "plant_wordlist.tsv"
QJ = ROOT / "综合词库.qj"
COPIES = [ROOT / "综合词库.tsv", ROOT / "综合词库.txt"]
COMMON = ROOT / "常用词" / "常用词.tsv"
WORDFREQ = ROOT / "常用词" / "爬取资料" / "stats" / "wordfreq.csv"

LADDER = {2: 380, 3: 365, 4: 352, 5: 340, 6: 330, 7: 322, 8: 315,
          9: 310, 10: 305, 11: 300, 12: 296}
SINGLE = 600

# df → 词频的分段锚点，由 常用词/常用词.tsv 与其 df 实测反推（各桶中位数）：
# df 60 落在 228、200 落在 288、800 落在 401、3200 落在 571、10000 落在 702。
# 语料里查得到 df 的植物名按此插值，它们才是真在用的。
DF_ANCHORS = [(1, 214), (30, 217), (60, 228), (100, 253), (200, 288),
              (400, 333), (800, 401), (1600, 480), (3200, 571),
              (10000, 702), (50000, 853)]

# 既有库读音确实错的植物名，按核定值覆盖。逐条核对过：
# 射干 yè gān（教育部《国语辞典》）、徐长卿 xú cháng qīng（药典）、
# 芫花 yán huā、羽扇槭 qì（《现代汉语词典》第七版 槭 单音 qì）、
# 参在五叶参/四叶参/刺参/拳参里读 shēn，子午莲的「子」是地支读本调。
PINYIN_FIX = {
    "五叶参": "wu3 ye4 shen1",
    "刺参": "ci4 shen1",
    "四叶参": "si4 ye4 shen1",
    "子午莲": "zi3 wu3 lian2",
    "射干": "ye4 gan4",
    "徐长卿": "xu2 chang2 qing1",
    "拳参": "quan2 shen1",
    "羽扇槭": "yu3 shan4 qi4",
    "芫花": "yan2 hua1",
    "黄柏": "huang2 bo4",
}

# 这几条植物库自己读错，不能覆盖综合库：
# 榅桲《现代汉语词典》作 wēn po（轻声），库内 wen1 po5 是对的；
# 枫茄花的「茄」取茄科义读 qié，库内按雪茄读成 jia1；
# 白朴是元曲四大家，与非洲朴的俗名同形，库内 bai2 pu3 不能改成 po4。
PINYIN_KEEP = {"榅桲", "枫茄花", "白朴"}

# 俗名里日常义压倒植物义的：词面在中文里另有高频含义，植物义几乎没人知道。
# 逐条回溯过 iPlant 来源（括号内为持有它的物种），确认都是真的地方叫法，
# 但收进综合库只会占掉日常候选的位次，与动物库剔除「花甲」「地铺」同理。
ALIAS_DROP = {
    "卡密",    # 小果白刺；网络用语「卡号密码」
    "大活",    # 白芷；东北话「大活儿」
    "打不死",   # 落地生根；口语
    "棉条",    # 紫穗槐；卫生用品
    "脚皮",    # 莲座紫金牛；口语
    "白车",    # 山蒲桃；口语
    "猪食",    # 长柄异药花；口语
    "沙和尚",   # 沙参；《西游记》人物
    "六甲",    # 飞蛾藤；干支、身怀六甲
    "三层楼",   # 变叶树参；口语
    "大绿",    # 鼠李；口语
    "鱼香",    # 留兰香；鱼香肉丝
    "蚂蚁窝",   # 短茎马先蒿；口语
    "半子",    # 半夏；口语
    "鸡骨头",   # 口语
    "八爪",    # 朱砂根；八爪鱼
    "铁花",    # 乌头；打铁花
    "鸭脚",    # 口语
    "五香",    # 香薷；五香粉
    "小红花",   # 朱唇；口语
    "老鼠屎",   # 口语
    "小白花",   # 口语
    "大果",    # 异木患；泛称
    "富贵花",   # 口语
    "白车",    # 山蒲桃；口语
    "冰粉",    # 假酸浆；甜品小吃
    "步步高",   # 步步高集团、口语
}

# 正名里日常义同样压倒植物义的。蓝月亮是马达加斯加千里光属的园艺名，
# 空竹是 Cephalostachyum latifolium 的中文正名，但日常语境里前者指洗衣液、
# 后者指抖空竹的玩具，收进输入法词库只会干扰。
NAME_DROP = {"蓝月亮", "空竹"}


def bare(py):
    return " ".join(s.rstrip("012345") for s in py.split(" "))


def load_qj():
    d = {}
    with io.open(QJ, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                d[p[0]] = (p[1], int(p[2]))
    return d


def load_wordlist():
    d = {}
    with io.open(WORDLIST, encoding="utf-8") as f:
        for line in f:
            w, py, kind, fr = line.rstrip("\n").split("\t")
            d[w] = (py, kind, int(fr))
    return d


def load_set(p):
    s = set()
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            q = line.rstrip("\n").split("\t")
            if len(q) >= 3:
                s.add(q[0])
    return s


def load_df():
    d = {}
    with io.open(WORDFREQ, encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) >= 3:
                d[row[0]] = int(row[1])
    return d


def tier(w, df):
    """按语料证据定档：查得到 df 的按锚点插值，查不到的按词长落在 296—380。

    单字植物名（姜、桃、茶、葱）在日常输入里是独立的高频字，统一 600。
    """
    if len(w) == 1:
        return SINGLE
    if w in df:
        return df_to_freq(df[w])
    return LADDER.get(len(w), 296)


def df_to_freq(d):
    if d <= DF_ANCHORS[0][0]:
        return DF_ANCHORS[0][1]
    for (x0, y0), (x1, y1) in zip(DF_ANCHORS, DF_ANCHORS[1:]):
        if d <= x1:
            t = (math.log10(d) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
            return int(round(y0 + t * (y1 - y0)))
    return DF_ANCHORS[-1][1]


def main(preview=False):
    base = load_qj()
    wl = load_wordlist()
    common = load_set(COMMON)
    df = load_df()
    before = len(base)
    print("综合库原有 %d 条，植物词表 %d 条" % (before, len(wl)))

    # 同码对手取既有词里词频最高的那个
    best = {}
    for w, (py, f) in base.items():
        c = bare(py)
        if c not in best or f > best[c][1]:
            best[c] = (w, f)

    added = alias_added = raised = unchanged = guarded = dropped = 0
    conflicts = []
    for w, (py, kind, _src) in wl.items():
        if w in NAME_DROP or (kind == "alias" and w in ALIAS_DROP):
            dropped += 1
            continue
        newpy = PINYIN_FIX.get(w, py)
        nf = tier(w, df)
        c = bare(newpy)
        if c in best and best[c][0] in common and nf > best[c][1]:
            nf = max(best[c][1] - 1, 150)
            guarded += 1

        if w in base:
            opy, ofreq = base[w]
            if kind == "alias":
                nf = ofreq
            newf = max(ofreq, nf)
            if newf > ofreq:
                raised += 1
            else:
                unchanged += 1
            if w not in PINYIN_KEEP and newpy != opy:
                conflicts.append((w, opy, newpy))
                opy = newpy
            base[w] = (opy, newf)
        else:
            base[w] = (newpy, nf)
            added += 1
            if kind == "alias":
                alias_added += 1

    print("新增 %d（其中俗名 %d），提频 %d，保持原值 %d，同码保护 %d，剔除 %d"
          % (added, alias_added, raised, unchanged, guarded, dropped))
    print("读音变更 %d 条" % len(conflicts))
    for c in sorted(conflicts):
        print("   %-10s %s -> %s" % c)
    print("合并后 %d 条，预期增量 %d" % (len(base), added))
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
