"""把 动物/动物.tsv 的中文名与俗名转成输入法词条：词面、拼音、来源标记、同名词数。"""
import io
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "动物/动物.tsv"
OUT = ROOT / ".omnicrawl/.agent_tmp/files/animal_entries.tsv"

HZ = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003ffff]+$")

# 俗名里的叙述残片、地名、分类阶元、泛称，不能当打字词条
ALIAS_STOP = {
    "东南亚", "之一", "北京", "西双版纳", "中国大鲵", "俗名鳀", "涡虫纲",
    "划分", "剥皮", "嘉宾", "天子", "大眼", "红眼", "白条", "铁甲", "飘飘",
    "相思", "墨鱼", "海龙", "天龙", "天马", "小巴", "刀片", "红枣", "鸡毛",
    "黑毛", "大虾", "黄鱼", "鳕鱼", "鸟", "禽", "猿", "触", "獭", "体延长",
    "长实", "长板", "长闹", "水长蛇", "长尾水鸟", "长脖佬", "还有猞猁",
    "溪的鸭", "有鹦鹆", "禽吉了", "有钩绦虫", "有瓜状头鲸", "之", "属", "科",
}

# 单字俗名会抢占极高频常用字，只保留确实常用的动物称名
SINGLE_KEEP = {"狐", "獭", "豕", "鼍", "鳖", "鲟", "鸮", "鹄", "鹊", "鹫", "鲛", "犴", "螱", "蚘"}

# 动物名里的多音字定音：pypinyin 在科名词组上系统性读错
CHAR_FIX = {
    "藏": "zang4",   # 藏狐、藏羚、西藏：西藏的藏
    "长": "chang2",  # 长尾、长吻、长臂：长短的长
    "重": "chong2",  # 重唇鱼、重齿：重叠的重
    "颈": "jing3",
    "氏": "shi4",
    "们": "men2",    # 图们江：地名 tún mén
    "鲌": "bo2",     # 翘嘴鲌、红鳍鲌：汉典 bó，非「鲅」的 bà
    "鮨": "yi4",
    "鳽": "jian1",   # 大麻鳽、苇鳽：鹭科鸟名 jiān
    "𫛚": "jian1",   # 鳽的类推简化字
    "𫚐": "yang1",   # 䱀属的类推简化字
    "𫚢": "yan3",    # 鰋的类推简化字
    "𫚪": "yu4",     # 鱊的类推简化字
}



WORD_FIX = {
    "大黄鱼": "da4 huang2 yu2",
    "犴": "an4",
    "鸟爪子": "niao3 zhua3 zi5",
    "铁爪子": "tie3 zhua3 zi5",
    "家雀": "jia1 qiao3",
    "山家雀儿": "shan1 jia1 qiao3 er2",
    "大山家雀儿": "da4 shan1 jia1 qiao3 er2",
    "绿林蛇": "lu4 lin2 she2",
    "模样河鲀": "mu2 yang4 he2 tun2",
    "成都": "cheng2 du1",
    "新都桥湍蛙": "xin1 du1 qiao2 tuan1 wa1",
    "都安岭鳅": "du1 an1 ling3 qiu1",
    "都安鲇": "du1 an1 nian2",
    "都庞岭半叶趾虎": "du1 pang2 ling3 ban4 ye4 zhi3 hu3",
    "马都拉叉牙𫚥虎": "ma3 du1 la1 cha1 ya2 xia1 hu3",
    "巴都盔鱼": "ba1 du1 kui2 yu2",
    "巴都鹦鲷": "ba1 du1 ying1 diao1",
    "都蜥蜴": "du1 xi1 yi4",
    "喀什麻蜥": "ka1 shi2 ma2 xi1",
    "克什米尔姬鼠": "ke4 shi2 mi3 er3 ji1 shu3",
    "哈什蟆": "ha1 shen2 ma2",
    "铅山壁虎": "yan2 shan1 bi4 hu3",
    "相模湾疣鲉": "xiang1 mo2 wan1 you2 you2",
    "相模湾眶灯鱼": "xiang1 mo2 wan1 kuang4 deng1 yu2",
    "相模眶灯鱼": "xiang1 mo2 kuang4 deng1 yu2",
    "棕胸佛法僧": "zong1 xiong1 fo2 fa3 seng1",
    "蓝胸佛法僧": "lan1 xiong1 fo2 fa3 seng1",
    "洪佛树蛙": "hong2 fu2 shu4 wa1",
    "金佛拟小鲵": "jin1 fu2 ni3 xiao3 ni2",
    "杉木条": "sha1 mu4 tiao2",
    "杉木鱼": "sha1 mu4 yu2",
    "细杉鱼": "xi4 shan1 yu2",
    "蛇口异星杉鱼": "she2 kou3 yi4 xing1 shan1 yu2",
    "拟红脖颈槽蛇": "ni3 hong2 bo2 jing3 cao2 she2",
    "果子狸": "guo3 zi5 li2",
    "扬子鳄": "yang2 zi5 e4",
    "知了": "zhi1 liao3",
    "白鹄": "bai2 hu2",       # 天鹅义读 hú，与既有库一致
    "匙嘴鹬": "chi2 zui3 yu4",  # 匙 读 chí
    "图们江": "tu2 men2 jiang1",
}



def load_rows():
    rows = []
    with io.open(SRC, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 3 and p[0]:
                rows.append(p)
    return rows


def to_pinyin(word):
    from pypinyin import pinyin, Style
    if word in WORD_FIX:
        return WORD_FIX[word]
    syl = [x[0] for x in pinyin(word, style=Style.TONE3, heteronym=False, errors="default")]
    if len(syl) != len(word) or not all(re.fullmatch(r"[a-z]+[1-5]?", s) for s in syl):
        syl = [pinyin(ch, style=Style.TONE3, heteronym=False, errors="default")[0][0]
               for ch in word]
    syl = [CHAR_FIX.get(ch, s) for ch, s in zip(word, syl)]
    out = []
    last = len(word) - 1
    for i, s in enumerate(syl):
        if not re.fullmatch(r"[a-z]+[1-5]?", s):
            raise ValueError("无读音: %r in %r" % (syl[i], word))
        if s in ("zi", "zi5"):
            # 「兔子」「石龙子」「篮子鱼」「梭子蟹」的子是词缀，读轻声；
            # 「子午沙鼠」「子鲚」的子作实义语素，读本调
            out.append("zi3" if i == 0 and last > 0 else "zi5")
        elif re.search(r"[1-5]$", s):
            out.append(s)
        else:
            out.append(s + "5")
    return " ".join(out)




def main():
    rows = load_rows()
    names = [r[0] for r in rows]
    alias = {}
    for r in rows:
        if r[2] == "-":
            continue
        for a in r[2].split("、"):
            alias.setdefault(a, []).append(r[0])

    entries = {}
    for n in names:
        entries[n] = ("name", 1)
    for a, owners in alias.items():
        if a in entries:
            entries[a] = ("both", entries[a][1])
        else:
            entries[a] = ("alias", len(owners))

    kept, dropped = {}, []
    for w, (kind, cnt) in entries.items():
        if not HZ.match(w):
            dropped.append((w, "非汉字"))
        elif len(w) == 1 and kind == "alias" and w not in SINGLE_KEEP:
            dropped.append((w, "单字俗名"))
        elif kind != "name" and w in ALIAS_STOP:
            dropped.append((w, "残片"))
        else:
            kept[w] = (kind, cnt)


    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for w in sorted(kept):
            kind, cnt = kept[w]
            f.write("%s\t%s\t%s\t%d\n" % (w, to_pinyin(w), kind, cnt))
    print("候选 %d，保留 %d，剔除 %d" % (len(entries), len(kept), len(dropped)))
    stat = {}
    for _, why in dropped:
        stat[why] = stat.get(why, 0) + 1
    print("剔除原因", stat)


if __name__ == "__main__":
    main()
