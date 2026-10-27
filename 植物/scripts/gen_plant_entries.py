"""把 植物/植物.tsv 的中文名与俗名转成输入法词条：词面 \\t 拼音 \\t 来源 \\t 同名词数。

来源标记：name = 名录正名，alias = 俗名。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "植物.tsv"))
OUT = os.path.join(HERE, "data", "plant_entries.tsv")

HZ = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003ffff]+$")

# 俗名里的叙述残片、地名、分类阶元与泛称，不能当打字词条
ALIAS_STOP = {
    "中国", "日本", "美国", "欧洲", "亚洲", "非洲", "美洲", "南方", "北方",
    "野生", "栽培", "品种", "变种", "变型", "亚种", "杂交", "原产", "引种",
    "一种", "一类", "某些", "少数", "其他", "等等", "以上", "以下",
    "各地", "各省", "地区", "我国", "全国", "常见", "普通", "一般",
}

# 单字俗名会抢占常用字，只保留确实会单独敲的
# 单字植物名：只保留日常会单独敲的（树名、作物、蔬菜、药草、竹木）
SINGLE_KEEP = set(
    "松柏杉柳杨槐榆桐桃杏李梅梨枣柿橘橙柚竹莲荷菊兰麻稻麦粟粱稷芋茄葱蒜韭"
    "姜芥苋艾茶桑漆樟栾榛栗榧桉梓楝楸莼菰荠蓟蓍藜荻蒲菅锥稗穇"
)

# 植物名里的多音字定音
CHAR_FIX = {
    "藏": "zang4",     # 西藏、藏报春
    "重": "chong2",    # 重瓣
    "长": "chang2",    # 长叶、长梗
    "芋": "yu4",
    "蓼": "liao3",
    "蓟": "ji4",
    "桧": "gui4",
    "朴": "po4",       # 朴树
    "柞": "zuo4",
    "芨": "ji1",
    "荠": "ji4",       # 荠菜 jì
    "苋": "xian4",
    "茜": "qian4",     # 茜草 qiàn
    "莎": "suo1",      # 莎草 suō
    "栎": "li4",
    "榉": "ju3",
    "杓": "biao1",     # 杓兰 biāo
    "芫": "yan2",      # 芫花 yán
    "蓖": "bi4",
    "藿": "huo4",
    "蓣": "yu4",
    "薤": "xie4",
    "莪": "e2",
    "荭": "hong2",
    "蘡": "ying1",
    "柽": "cheng1",
    "檵": "ji4",
    "檫": "cha2",
    "樾": "yue4",
    "芡": "qian4",
    "茝": "chai3",
    "薜": "bi4",
    "茼": "tong2",
    "荽": "sui1",
    "苜": "mu4",
    "蓿": "xu5",
    "柃": "ling2",
    "椴": "duan4",
    "槭": "qi4",
    "桉": "an1",
    "榅": "wen1",
    "桲": "bo2",
    "参": "shen1",
}

WORD_FIX = {
    "朴树": "po4 shu4",
    "荠菜": "ji4 cai4",
    "莎草": "suo1 cao3",
    "茜草": "qian4 cao3",
    "白术": "bai2 zhu2",
    "苍术": "cang1 zhu2",
    "厚朴": "hou4 po4",
    "黄柏": "huang2 bo2",
    "柏树": "bai3 shu4",
    "侧柏": "ce4 bai3",
    "荸荠": "bi2 qi2",
    "菡萏": "han4 dan4",
    "茉莉": "mo4 li4",
    "蔷薇": "qiang2 wei1",
    "玫瑰": "mei2 gui1",
    "月季": "yue4 ji4",
    "牡丹": "mu3 dan1",
    "参三七": "shen1 san1 qi1",
    "珠子参": "zhu1 zi5 shen1",
    "竹节参": "zhu2 jie2 shen1",
    "拳参": "quan2 shen1",
    "树参": "shu4 shen1",
    "玄参": "xuan2 shen1",
    "还阳参": "huan2 yang2 shen1",
    "婆罗门参": "po2 luo2 men2 shen1",
    "一掌参": "yi1 zhang3 shen1",
    "茄": "qie2",
    "屈曲花": "qu1 qu3 hua1",
    "芍药": "shao2 yao4",
    "芫荽": "yan2 sui1",
    "薄荷": "bo4 he2",
    "萝藦": "luo2 mo4",
    "桔梗": "jie2 geng3",
    "桔子": "ju2 zi5",
    "枸橼": "ju3 yuan2",
    "枸杞": "gou3 qi3",
    "枸骨": "gou3 gu3",
    "荠苨": "ji4 ni2",
    "荸荠莲": "bi2 qi5 lian2",
    "苘麻": "qing3 ma2",
    "莙荙": "jun4 da2",
    "蘡薁": "ying1 yu4",
    "蘘荷": "rang2 he2",
    "箬竹": "ruo4 zhu2",
    "筇竹": "qiong2 zhu2",
    "茳芏": "jiang1 du4",
    "蔊菜": "han4 cai4",
    "莼菜": "chun2 cai4",
    "蕹菜": "weng4 cai4",
    "荠菜花": "ji4 cai4 hua1",
    "蕺菜": "ji2 cai4",
}


def to_pinyin(word):
    from pypinyin import pinyin, Style
    if word in WORD_FIX:
        return WORD_FIX[word]
    syl = [x[0] for x in pinyin(word, style=Style.TONE3, heteronym=False, errors="default")]
    if len(syl) != len(word) or not all(re.fullmatch(r"[a-z]+[1-5]?", s) for s in syl):
        syl = [pinyin(ch, style=Style.TONE3, heteronym=False, errors="default")[0][0] for ch in word]
    syl = [CHAR_FIX.get(ch, s) for ch, s in zip(word, syl)]
    out = []
    for i, s in enumerate(syl):
        if not re.fullmatch(r"[a-z]+[1-5]?", s):
            raise ValueError("无读音: %r" % word)
        if s in ("zi", "zi5"):
            out.append("zi3" if i == 0 and len(word) > 1 else "zi5")
        elif re.search(r"[1-5]$", s):
            out.append(s)
        else:
            out.append(s + "5")
    return " ".join(out)


def main():
    rows = []
    with io.open(SRC, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0]:
                rows.append(p)

    alias = {}
    for p in rows:
        if p[2] == "-":
            continue
        for a in p[2].split("、"):
            if a:
                alias.setdefault(a, []).append(p[0])

    entries = {}
    for p in rows:
        entries[p[0]] = ("name", 1)
    for a, owners in alias.items():
        if a in entries:
            entries[a] = ("both", entries[a][1])
        else:
            entries[a] = ("alias", len(owners))

    kept, dropped, bad = {}, [], []
    for w, (kind, cnt) in entries.items():
        if not HZ.match(w):
            dropped.append((w, "非汉字"))
        elif len(w) == 1 and w not in SINGLE_KEEP:
            dropped.append((w, "单字"))
        elif kind != "name" and w in ALIAS_STOP:
            dropped.append((w, "残片"))
        elif len(w) > 12:
            dropped.append((w, "过长"))
        else:
            kept[w] = (kind, cnt)

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for w in sorted(kept):
            kind, cnt = kept[w]
            try:
                py = to_pinyin(w)
            except ValueError:
                bad.append(w)
                continue
            f.write("%s\t%s\t%s\t%d\n" % (w, py, kind, cnt))
    print("候选 %d 保留 %d 剔除 %d 无读音 %d" % (len(entries), len(kept) - len(bad), len(dropped), len(bad)))
    st = {}
    for _, why in dropped:
        st[why] = st.get(why, 0) + 1
    print("剔除原因", st)
    if bad:
        print("无读音样例", bad[:10])


if __name__ == "__main__":
    main()
