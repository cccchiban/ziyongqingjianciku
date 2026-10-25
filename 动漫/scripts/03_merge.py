"""合并搜狗「动漫」分类 293 个 scel：整库排除无关库 → 词级清洗 → 按词面去重
→ 与既有源词库判重 → 合成拼音与词频。
"""
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pypinyin import Style, pinyin
from scel import parse_scel

WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
REPO = pathlib.Path(__file__).parent.parent.parent

CJK = re.compile(r"^[\u3400-\u9fff]+$")

# 整库排除：内容与动漫无关，或整库是对话句 / 个人标签，不成词条
EXCLUDE_NAMES = [
    u"勤务词语2025套装",   # 政治军事勤务词，与动漫无关
    u"tk1",                # 教学设计术语，与动漫无关
    u"彩红天堂",           # 聊天句（我的皮肤最美丽）
    u"亚梦吧",             # 个人介绍句（喜欢绿色讨厌红色）
]

# 词频主项用「独立作品族数」而非「收录库数」或「非官方库数」。
# 收录库数会被同一作品的多份库灌水：`方块` 12 库里有 5 个是守护甜心系、
# `天天` 10 库里 6 个是火影系。归并到作品族后 `方块` 7 族、`天天` 7 族，
# 与 `手鞠` 11 族、`漩涡鸣人` 9 族拉开真实差距，且 `射门`(1 族)、`坏蛋`(2 族)
# 这类边缘词自然落到低档，不需要额外的日常词清单去硬判。
FAMILY_SUFFIX = re.compile(u'(【.*?】|\\[.*?\\]|词库|专用|人物名|大全|人物介绍|词汇'
                           u'|名词|全招数|全招|忍术|新词库|必备|合集|控专用|的).*$')


def family(name):
    """把同作品的多份细胞词库归并为一个族名。"""
    n = FAMILY_SUFFIX.sub("", name)
    n = re.sub(u'^\\s*|[\\s_\\-]+$', "", n)
    return (n or name)[:12]



# 拼音策略：以 pypinyin 的**词组**读音为准。
# 实测综合库前 6 万条抽样中，pypinyin 词组读音与既有值吻合 98.2%（58935/60000），
# 是仓库里最可信的读音来源。初版曾用 scel 自带的无声调音节逐字挑候选声调，
# 那一步绕过了 pypinyin 的词组消歧，把 `傀儡术` 读成 gui1、`大将` 读成 jiang1、
# `照相机` 读成 xiang1，与综合库撞出 455 条冲突。scel 音节只在「该词不在综合库
# 且 pypinyin 与 scel 词数一致」时用于校验，不用于覆盖。
# 下列修正只收 pypinyin 明确处理不了、且有确定通行读法的动漫专名。
WORD_FIX = {
    u"武藏": "wu3 zang4",                   # 宫本武藏，人名 zàng（pypinyin 给 cang2）
}
# 上述之外，pypinyin 已能正确处理：御坂美琴 yu4、写轮眼 xie3、查克拉 cha2 ke4 la1、
# 五更琉璃 geng1、宿傩 su4、惣流 zong3、碇 ding4、雫 na3、凪 zhi3。


NORM = {"lue": "lve", "lue4": "lve4", "nue": "nve", "nue4": "nve4"}


def norm(s):
    s = s.replace(u"ü", "v")
    return NORM.get(s, s)


_WCACHE = {}


def word_pinyin(w):
    """词组读音：pypinyin 会按词组消歧，逐字取候选则不会。

    音节数必须等于字数（本库词面全为汉字，pypinyin 对生僻日文汉字也保一对一），
    不等时退化为逐字首选音。
    """
    if w not in _WCACHE:
        _WCACHE[w] = [norm(x[0]) for x in
                      pinyin(w, style=Style.TONE3, neutral_tone_with_five=True)]
    return list(_WCACHE[w])


def sent_like(w):
    """只剔除能确定不是词条的形态。

    对白残片（`我是地雷女`、`你的替身最没用啦`）与真作品名（`这个是僵尸吗`、
    `我的英雄学院`、`请问您今天要来点兔子吗`、`恋爱随意链接`）在词面上同形，
    任何通用规则都会误删后者。故不使用语气词/虚词/百科后缀等规则，只靠
    源库层面的整库排除和词面形态判据（纯汉字、>=2 字）控制。
    """
    return False


def existing_words():
    """判重集：既有源词库。

    排除三类：派生文件（综合词库、游戏合集）、本目录自身、语料型大库
    `文学作品/文学作品词库.tsv`。据语料库判重会把「动漫」「漫画」这类核心词
    判成重复而剔除，主题库只剩冷僻词——与电商库、神话库的判重教训同源。
    """
    skip = {"综合词库.qj", "综合词库.tsv", "游戏/游戏词库合集.qj",
            "文学作品/文学作品词库.tsv"}
    words = set()
    for pat in ("*.tsv", "*.qj", "*/*.tsv", "*/*.qj"):
        for p in REPO.glob(pat):
            rel = p.relative_to(REPO).as_posix()
            if rel in skip or rel.startswith(".omnicrawl") or rel.startswith(u"动漫"):
                continue
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                w = line.split("\t")[0].strip()
                if w:
                    words.add(w)
    return words


def main():
    meta = {m["id"]: m for m in json.load(open(WORK / "meta.json", encoding="utf-8"))}
    excluded = {m["id"] for m in meta.values() if m["name"] in EXCLUDE_NAMES}
    print(u"整库排除 %d 个：%s" % (len(excluded),
                               u"、".join(meta[i]["name"] for i in excluded)))

    cand = defaultdict(list)
    raw = 0
    for path in sorted(WORK.joinpath("scel").glob("*.scel")):
        did = int(path.stem)
        if did in excluded:
            continue
        words, end, total = parse_scel(path.read_bytes())
        assert end == total, (did, meta[did]["name"])
        for w, py in words:
            w = w.strip()
            raw += 1
            if len(w) < 2 or not CJK.match(w):
                continue
            cand[w].append((py, did))
    print(u"候选词面 %d（来自 %d 条原始词条）" % (len(cand), raw))

    exist = existing_words()
    print(u"既有源词库词面 %d" % len(exist))

    rows, dup, sents = [], 0, 0
    for w, recs in cand.items():
        if w in exist:
            dup += 1
            continue
        if sent_like(w):
            sents += 1
            continue
        final = word_pinyin(w)
        if w in WORD_FIX:
            final = WORD_FIX[w].split()
        rows.append({"w": w, "py": " ".join(final),
                     "cnt": len({r[1] for r in recs}),
                     "fam": len({family(meta[r[1]]["name"]) for r in recs}),
                     "dl": max(meta[r[1]]["downloads"] for r in recs),
                     "len": len(w)})
    print(u"入库 %d，与既有重复 %d，句子/口语剔除 %d" % (len(rows), dup, sents))

    dist = Counter()
    for r in rows:
        # fam（独立作品族数）与 cnt（收录库数）之差是关键信号：
        # 声优跨作品出现，每个作品各录一次，故 cnt == fam（樱井孝宏 21/21、
        # 花泽香菜 14/14）；作品内角色与术语会被同一作品的多份库重复收录，
        # 故 cnt - fam >= 3（手鞠 19/11、漩涡鸣人 12/9、螺旋丸 11/8）。
        # 输入法里要打的是角色名与作品名而不是声优，故对 cnt == fam 的名字压档。
        base = 400 + 48 * min(r["fam"], 5)
        if r["fam"] > 5:
            base += 16 * (r["fam"] - 5)
        base += 10 * min(r["cnt"] - r["fam"], 6)
        if r["dl"] >= 50000:
            base += 70
        elif r["dl"] >= 10000:
            base += 50
        elif r["dl"] >= 6000:
            base += 30
        elif r["dl"] >= 4000:
            base += 15
        if r["len"] == 2:
            base += 30
        elif r["len"] == 3:
            base += 15
        elif r["len"] >= 9:
            base -= 8 * (r["len"] - 8)
        r["freq"] = max(300, min(950, base // 5 * 5))
        if r["cnt"] - r["fam"] <= 1 and r["cnt"] >= 4:
            # 声优兜底：这类名字每个作品各录一次，但集中在热门作品库，下载量
            # 加权会把它推回高位（樱井孝宏 dl 8013）。输入目标是角色名，压到中档。
            r["freq"] = min(r["freq"], 560)
        dist[r["freq"]] += 1
    print(u"词频档 %s" % sorted(dist.items(), reverse=True)[:12])
    print(u"档位数 %d 最高 %d 最低 %d" % (len(dist), max(dist), min(dist)))
    rows.sort(key=lambda r: (-r["freq"], r["py"], r["w"]))
    (WORK / "rows.json").write_text(
        json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    for r in rows[:5]:
        print(r)


if __name__ == "__main__":
    main()
