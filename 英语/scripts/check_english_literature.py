# -*- coding: utf-8 -*-
"""校验 英语/文学/英语文学词库.tsv。

除常规格式检查外，重点审多音字与音译专名：列出所有拼音，供人工比对；
并对已知易错字给出期望读音表，偏差一律列出。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TARGET = os.path.join(REPO, "英语", "文学", "英语文学词库.tsv")

HAN = re.compile(r"^[\u3400-\u9fff]+$")
SYL = re.compile(r"^([a-z]+[1-5]|[A-Za-z0-9])$")

# 易错读音期望表：词面 -> {字序号: 期望带调音节}
EXPECT = {
    "狄更斯": "di2 geng1 si1",
    "乔叟": "qiao2 sou3",
    "华兹华斯": "hua2 zi1 hua2 si1",
    "柯勒律治": "ke1 le4 lv4 zhi4",
    "萨克雷": "sa4 ke4 lei2",
    "哈代": "ha1 dai4",
    "丁尼生": "ding1 ni2 sheng1",
    "王尔德": "wang2 er3 de2",
    "赫胥黎": "he4 xu1 li2",
    "吉卜林": "ji2 bu3 lin2",
    "康拉德": "kang1 la1 de2",
    "伍尔夫": "wu3 er3 fu1",
    "乔伊斯": "qiao2 yi1 si1",
    "爱默生": "ai4 mo4 sheng1",
    "梭罗": "suo1 luo2",
    "霍桑": "huo4 sang1",
    "梅尔维尔": "mei2 er3 wei2 er3",
    "狄金森": "di2 jin1 sen1",
    "马克吐温": "ma3 ke4 tu3 wen1",
    "菲茨杰拉德": "fei1 ci2 jie2 la1 de2",
    "海明威": "hai3 ming2 wei1",
    "福克纳": "fu2 ke4 na4",
    "斯坦贝克": "si1 tan3 bei4 ke4",
    "塞林格": "sai1 lin2 ge2",
    "冯内古特": "feng2 nei4 gu3 te4",
    "贝娄": "bei4 lou2",
    "厄普代克": "e4 pu3 dai4 ke4",
    "麦克尤恩": "mai4 ke4 you2 en1",
    "石黑一雄": "shi2 hei1 yi1 xiong2",
    "鲁西迪": "lu3 xi1 di2",
    "奈保尔": "nai4 bao3 er3",
    "莱辛": "lai2 xin1",
    "拜厄特": "bai4 e4 te4",
    "叶芝": "ye4 zhi1",
    "贝克特": "bei4 ke4 te4",
    "希尼": "xi1 ni2",
    "奥登": "ao4 deng1",
    "拉金": "la1 jin1",
    "弥尔顿": "mi2 er3 dun4",
    "班扬": "ban1 yang2",
    "德莱顿": "de2 lai2 dun4",
    "斯威夫特": "si1 wei1 fu1 te4",
    "笛福": "di2 fu2",
    "菲尔丁": "fei1 er3 ding1",
    "斯特恩": "si1 te4 en1",
    "勃朗宁": "bo2 lang3 ning2",
    "阿诺德": "a1 nuo4 de2",
    "罗斯金": "luo2 si1 jin1",
    "萧伯纳": "xiao1 bo2 na4",
    "柯南道尔": "ke1 nan2 dao4 er3",
    "斯蒂文森": "si1 di4 wen2 sen1",
    "卡罗尔": "ka3 luo2 er3",
    "格雷": "ge2 lei2",
    "布莱克": "bu4 lai2 ke4",
    "彭斯": "peng2 si1",
    "骚塞": "sao1 sai1",
    "拜伦": "bai4 lun2",
    "雪莱": "xue3 lai2",
    "济慈": "ji4 ci2",
    "奥斯汀": "ao4 si1 ting1",
    "司各特": "si1 ge4 te4",
    "梅瑞狄斯": "mei2 rui4 di2 si1",
    "特罗洛普": "te4 luo2 luo4 pu3",
    "盖斯凯尔": "gai4 si1 kai3 er3",
    "爱伦坡": "ai4 lun2 po1",
    "惠特曼": "hui4 te4 man4",
    "庞德": "pang2 de2",
    "艾略特": "ai4 lve4 te4",
    "弗罗斯特": "fu2 luo2 si1 te4",
    "史蒂文斯": "shi3 di4 wen2 si1",
    "金斯堡": "jin1 si1 bao3",
    "凯鲁亚克": "kai3 lu3 ya4 ke4",
    "巴勒斯": "ba1 le4 si1",
    "品钦": "pin3 qin1",
    "海勒": "hai3 le4",
    "梅勒": "mei2 le4",
    "莫里森": "mo4 li3 sen1",
    "鲍德温": "bao4 de2 wen1",
    "赖特": "lai4 te4",
    "赫斯顿": "he4 si1 dun4",
    "麦卡勒斯": "mai4 ka3 le4 si1",
    "奥康纳": "ao4 kang1 na4",
    "德里罗": "de2 li3 luo2",
    "麦卡锡": "mai4 ka3 xi1",
    "多克托罗": "duo1 ke4 tuo1 luo2",
    "欧文": "ou1 wen2",
    "库珀": "ku4 po4",
    "华莱士": "hua2 lai2 shi4",
    "乔叟": "qiao2 sou3",
}


def main():
    bad = 0
    raw = io.open(TARGET, "rb").read()
    if b"\r" in raw:
        print("含 CRLF"); bad += 1
    if not raw.endswith(b"\n"):
        print("末行无换行"); bad += 1

    rows, seen = [], {}
    for ln, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if line.count("\t") != 2:
            print("%d 字段数不是 3: %r" % (ln, line)); bad += 1; continue
        w, py, fr = line.split("\t")
        if " " in w:
            print("%d 词面含空格: %r" % (ln, w)); bad += 1
        if not fr.isdigit() or int(fr) <= 0:
            print("%d 词频非正整数: %r" % (ln, fr)); bad += 1
        syls = py.split(" ")
        if len(syls) != len(w):
            print("%d 音节数 %d != 字数 %d: %s %s" % (ln, len(syls), len(w), w, py))
            bad += 1
        for s in syls:
            if not SYL.match(s):
                print("%d 非法音节: %r (%s)" % (ln, s, w)); bad += 1
        if w.lower() in seen:
            print("%d 词面重复（另见 %d）: %s" % (ln, seen[w.lower()], w)); bad += 1
        seen[w.lower()] = ln
        rows.append((w, py, int(fr)))

    if rows != sorted(rows, key=lambda r: (-r[2], r[1], r[0])):
        print("排序不符合「词频降序→拼音→词面」"); bad += 1

    freq = [r[2] for r in rows]
    print("%d 条，词频 %d—%d" % (len(rows), min(freq), max(freq)))

    got = {r[0]: r[1] for r in rows}
    miss = [w for w in EXPECT if w not in got]
    if miss:
        print("期望表中不在库里的词（无妨，仅提示）:", " ".join(miss))
    diff = [(w, EXPECT[w], got[w]) for w in EXPECT if w in got and got[w] != EXPECT[w]]
    if diff:
        print("读音偏差 %d 条：" % len(diff))
        for w, e, g in diff:
            print("  %-10s 期望 %-26s 实际 %s" % (w, e, g))
        bad += len(diff)
    else:
        print("读音偏差 0 条")
    print("结论:", "通过" if bad == 0 else "失败 %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
