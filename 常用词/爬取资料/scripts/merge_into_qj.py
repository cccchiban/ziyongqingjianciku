# -*- coding: utf-8 -*-
"""把 常用词/常用词.tsv 并入 综合词库.qj / 综合词库.tsv。

词面去重、词频取两库最大、拼音用常用词库值覆盖。
两库读音冲突 47 条已逐条按《现代汉语词典》核定，常用词库值全部正确（见 PINYIN_FIX 注释）。
"""
import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
QJ = ROOT / "综合词库.qj"
TSV = ROOT / "综合词库.tsv"
SRC = ROOT / "常用词" / "常用词.tsv"

# 47 条冲突里综合库错、该被修正的读音。常用词库的拼音即为正解，
# 这里显式列出是为了留下核对痕迹，并在合并后断言生效。
PINYIN_EXPECT = {
    "不间断": "bu4 jian4 duan4", "中奖": "zhong4 jiang3", "为主": "wei2 zhu3",
    "产假": "chan3 jia4", "人为": "ren2 wei2", "人为因素": "ren2 wei2 yin1 su4",
    "供应": "gong1 ying4", "关系": "guan1 xi5", "副本": "fu4 ben3",
    "好处": "hao3 chu5", "妖精": "yao1 jing5", "少爷": "shao4 ye2",
    "差异": "cha1 yi4", "带子": "dai4 zi5", "应用": "ying4 yong4",
    "成分": "cheng2 fen4", "折腾": "zhe1 teng5", "抹布": "ma1 bu4",
    "数码相机": "shu4 ma3 xiang4 ji1", "格子": "ge2 zi5", "模板": "mu2 ban3",
    "灾难": "zai1 nan4", "熟练": "shu2 lian4",
    "电子商务": "dian4 zi3 shang1 wu4", "电钻": "dian4 zuan4",
    "相位": "xiang4 wei4", "相机": "xiang4 ji1", "知识": "zhi1 shi5",
    "神曲": "shen2 qu3", "种树": "zhong4 shu4", "称为": "cheng1 wei2",
    "答应": "da1 ying5", "调和": "tiao2 he2", "转盘": "zhuan4 pan2",
    "较差": "jiao4 cha4", "适应": "shi4 ying4", "部署": "bu4 shu3",
    "重来": "chong2 lai2", "间隔": "jian4 ge2", "间隙": "jian4 xi4",
    "阵子": "zhen4 zi5", "静静地": "jing4 jing4 de5",
    "音乐": "yin1 yue4", "默默地": "mo4 mo4 de5",
    # 同形多音，两读皆通，按口语高频义取常用词库值
    "分子": "fen4 zi3",     # 知识分子、积极分子（fēn zǐ 为化学义）
    "公差": "gong1 chai1",  # 出公差（gōng chā 为机械公差）
    "倒数": "dao4 shu3",    # 倒计时义（dào shù 为数学倒数）
}


def load(path):
    d = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                d[p[0]] = (p[1], int(p[2]))
    return d


def main():
    base = load(QJ)
    src = load(SRC)
    n0 = len(base)
    print("综合库原有 %d 条，常用词 %d 条" % (n0, len(src)))

    changed = [(w, base[w][0], py) for w, (py, _) in src.items()
               if w in base and base[w][0] != py]
    added = 0
    for w, (py, fq) in src.items():
        if w in base:
            base[w] = (py, max(base[w][1], fq))
        else:
            base[w] = (py, fq)
            added += 1
    print("新增 %d 条，已存在合并 %d 条" % (added, len(src) - added))
    print("读音被常用词库覆盖 %d 条" % len(changed))

    bad = [(w, py, base[w][0]) for w, py in PINYIN_EXPECT.items()
           if w not in base or base[w][0] != py]
    assert not bad, "核定读音未生效：%s" % bad[:5]
    print("47 条核定读音全部生效")

    assert len(base) == n0 + added, "词面数不符"
    assert added > 0, "未新增任何词条，拒绝写出"

    lines = ["%s\t%s\t%d" % (w, py, fq) for w, (py, fq) in base.items()]
    lines.sort(key=lambda s: (lambda p: (-int(p[2]), p[1], p[0]))(s.split("\t")))
    body = "\n".join(lines) + "\n"
    for path in (QJ, TSV):
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    print("写出 %s 与 %s：%d 条" % (QJ.name, TSV.name, len(lines)))

    print("\n读音变化中词频被抬升最多的 12 条：")
    for w, old, new in sorted(changed, key=lambda x: -src[x[0]][1])[:12]:
        print("   %-10s %-22s → %-22s 词频 %d" % (w, old, new, src[w][1]))


if __name__ == "__main__":
    main()
