"""合并 59 个电力电气 scel：整库排除 → 词面去重 → 与既有源库判重 → 合成拼音与词频。"""
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
ORG = re.compile(u"(有限公司|股份公司|股份有限公司|有限责任公司|集团|分厂|制造厂|电器厂|电缆厂)$")

# 整库排除：企业名录、地域线路名、检修记录、个人工作档，以及内容非电力的库
EXCLUDE_NAMES = [
    u"电力设备企业名录",       # 1415 条，全是公司名
    u"电力线路",               # 455 条，全是地域线路名（阿产线、包一线）
    u"我QJ的工作",             # 19 条，个人工作范围内的变电站名
    u"锡电标准化",             # 29 条，供电分局名与个人姓名
    u"by",                     # 12 条，检修部门名
    u"发电设备管理",           # 33 条，故障描述句（齿轮油泵损坏）
    u"柜体盘厂用名词",         # 96 条，厂内工艺术语与个人姓名混排（金人、丧假）
    u"骆驼蓄电池",             # 155 条，企业车间用语与品牌名
    u"TFT-LCD工艺",            # 281 条，面板厂工艺术语，非电力
    u"装饰工程",               # 5 条，人名为首的工程报价词
    u"河南和青电力工程有限公司",
    u"廊坊北熔电气",
    u"欣蓬砝码 铸铁砝码 不锈钢砝码",
    u"电工电气",               # 5 条，上海通士电气品牌名
    u"步进电机",               # 5 条，汉德保品牌型号
    u"断路器的选择",           # 6 条，全是「表示回路里面可以装位的断路器」这类句子
    u"车载电力工程学",         # 3 条，句子
    u"行业专业术语",           # 9 条，含饲料添加剂，跨领域
    u"电话通信",               # 51 条，呼叫中心系统配置词
]

# scel 音节与 pypinyin 默认读音不一致的多音字，取 scel 音节（行业实际读法）
SINGLE = {
    "重": ["chong2", "zhong4"], "调": ["tiao2", "diao4"], "长": ["chang2", "zhang3"],
    "轧": ["zha2", "ya4"], "弹": ["tan2", "dan4"], "扎": ["za1", "zha1"],
    "粘": ["nian2", "zhan1"], "模": ["mu2", "mo2"], "掺": ["chan1", "can4"],
    "称": ["chen4", "cheng1"], "着": ["zhuo2", "zhao2", "zhe5"], "校": ["jiao4", "xiao4"],
    "薄": ["bo2", "bao2"], "栅": ["shan1", "zha4"], "行": ["hang2", "xing2"],
    "壳": ["qiao4", "ke2"], "识": ["zhi4", "shi2"], "龟": ["jun1", "gui1"],
    "剥": ["bao1", "bo1"], "削": ["xiao1", "xue1"], "勒": ["le4", "lei1"],
    "塞": ["se4", "sai1"], "辗": ["zhan3", "nian3"], "朝": ["zhao1", "chao2"],
    "地": ["de5", "di4"], "刨": ["bao4", "pao2"], "伺": ["si4", "ci4"],
    "给": ["ji3", "gei3"], "露": ["lou4", "lu4"], "没": ["mo4", "mei2"],
    "泊": ["bo2", "po1"], "镦": ["dun1", "dui1"], "爪": ["zhua3", "zhao3"],
    "炔": ["que1", "gui4"], "还": ["huan2", "hai2"], "似": ["si4", "shi4"],
    "色": ["shai3", "se4"], "略": ["lve4", "lue4"], "卡": ["qia3", "ka3"],
    "曝": ["bao4", "pu4"], "省": ["xing3", "sheng3"], "属": ["zhu3", "shu3"],
    "传": ["zhuan4", "chuan2"], "便": ["pian2", "bian4"], "什": ["shi2", "shen2"],
    "熟": ["shou2", "shu2"], "恶": ["wu4", "e4"], "柏": ["bo2", "bai3"],
    "迫": ["pai3", "po4"], "囤": ["tun2", "dun4"], "攒": ["cuan2", "zan3"],
    "落": ["lao4", "luo4"], "率": ["shuai4", "lv4"], "仔": ["zi3", "zai3"],
    "藏": ["zang4", "cang2"], "龟": ["jun1", "gui1"], "茄": ["qie2", "jia1"],
    "琢": ["zhuo2", "zuo2"], "和": ["huo4", "he2"], "吓": ["he4", "xia4"],
    "解": ["xie4", "jie3"], "单": ["shan4", "dan1"], "参": ["cen1", "can1"],
    "肋": ["lei4", "le1"], "兹": ["ci2", "zi1"], "纤": ["qian4", "xian1"],
    "匙": ["chi2", "shi5"], "蚌": ["beng4", "bang4"], "钥": ["yue4", "yao4"],
    "了": ["liao3", "le5"], "差": ["cha1", "chai1", "ci1"], "都": ["du1", "dou1"],
    "奇": ["ji1", "qi2"], "会": ["kuai4", "hui4"], "角": ["jue2", "jiao3"],
}
NORM = {"lue": "lve", "lue4": "lve4", "nue": "nve", "nue4": "nve4"}

# 通行读音，纠正 scel 源标注错误
SYL_FIX = {
    "识": {"zhi": "shi2"},   # 标识 biao1 shi2
    "钥": {"yue": "yao4"},   # 密钥 mi4 yao4
    "轧": {"ya": "zha2"},    # 轧制 zha2 zhi4
}
WORD_FIX = {
    "标么值": "biao1 yao1 zhi2",
    "标么制": "biao1 yao1 zhi4",
}

# 术语里读本调、不读轻声的字（pypinyin 默认给轻声）
NO_NEUTRAL = {"子": "zi3", "么": "me5", "地": "di4"}


def norm(s):
    s = s.replace("ü", "v")
    return NORM.get(s, s)


def bare(s):
    return norm("".join(c for c in s if not c.isdigit()))


def fix_syllables(word, syllables):
    if word in WORD_FIX:
        return WORD_FIX[word].split()
    out = []
    for ch, s in zip(word, syllables):
        s = norm(s)
        s = SYL_FIX.get(ch, {}).get(bare(s), s)
        if s.endswith("5") and ch in NO_NEUTRAL and ch != "么":
            s = NO_NEUTRAL[ch]
        out.append(s)
    return out


_CCACHE = {}


def tone_cands(word):
    out = []
    for ch in word:
        if ch in SINGLE:
            out.append(SINGLE[ch])
            continue
        if ch not in _CCACHE:
            _CCACHE[ch] = [norm(x[0]) for x in
                           pinyin(ch, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)]
        out.append(_CCACHE[ch])
    return out


def glued(word):
    """词典把两个译名并列写成一条（…拒收数…拒收数），不是可输入词条。"""
    n = len(word)
    if n < 12:
        return False
    for k in range(4, n - 3):
        head, tail = word[:k], word[k:]
        if len(tail) < 4:
            break
        common = len(set(head) & set(tail))
        if common >= 3 and common * 2 >= min(len(head), len(tail)):
            return True
    return False


REPEAT = re.compile(r"(.{2})\1(.{2})")


def repeated(word):
    """「放线放线装置」「名名称」这类词头重复成词，是词表截断后的拼接。"""
    if len(word) >= 6 and REPEAT.search(word):
        return True
    return len(set(word)) * 2 <= len(word) and len(word) >= 4


VERBAL = re.compile(u".*的(显示|进行|作用|方法|使用|工作|运行|试验|测试|检查|维护|安装|制造|加工|选择|处理)$")


def syncretic(word):
    """同义术语并列写成一条（复用器解复用器、镍包铜线镀镍铜线），是词表拼接。"""
    n = len(word)
    for k in range(3, n - 2):
        a, b = word[:k], word[k:]
        if a in b or b in a:
            return True
    return False


def procedural(word):
    """工艺说明句（点火枪的安装、汽包的作用），不是词条。"""
    return bool(VERBAL.match(word))


def chatty(word):
    if word.startswith((u"请您", u"请插", u"请将", u"请按", u"请点", u"请选择", u"请检查",
                        u"请确认", u"请稍", u"请重", u"请先", u"请关", u"请输", u"请使用")):
        return True
    return word[-1] in u"吧吗呢"


def existing_words():
    skip = {"综合词库.qj", "综合词库.tsv", "游戏/游戏词库合集.qj"}
    words = set()
    for pat in ("*.tsv", "*.qj", "*/*.tsv", "*/*.qj"):
        for p in REPO.glob(pat):
            rel = p.relative_to(REPO).as_posix()
            if rel in skip or rel.startswith(".omnicrawl") or rel.startswith("电力电气"):
                continue
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                w = line.split("\t")[0].strip()
                if w:
                    words.add(w)
    return words


def main():
    meta = {m["id"]: m for m in json.load(open(WORK / "meta.json", encoding="utf-8"))}
    excluded = {m["id"] for m in meta.values() if m["name"] in EXCLUDE_NAMES}
    print("整库排除", len(excluded), "个：", "、".join(meta[i]["name"] for i in excluded))

    cand = defaultdict(list)
    for path in sorted(WORK.joinpath("scel").glob("*.scel")):
        did = int(path.stem)
        if did in excluded:
            continue
        words, end, total = parse_scel(path.read_bytes())
        assert end == total, (did, meta[did]["name"])
        for w, py in words:
            w = w.strip()
            if len(w) < 2 or not CJK.match(w) or ORG.search(w):
                continue
            cand[w].append((py, did))
    print("候选词面", len(cand))

    exist = existing_words()
    print("既有词面", len(exist))

    rows, dup, skip = [], 0, Counter()
    for w, recs in cand.items():
        if w in exist:
            dup += 1
            continue
        if glued(w):
            skip["glued"] += 1
            continue
        if chatty(w):
            skip["chatty"] += 1
            continue
        if repeated(w):
            skip["repeated"] += 1
            continue
        if syncretic(w):
            skip["syncretic"] += 1
            continue
        if procedural(w):
            skip["procedural"] += 1
            continue
        py, did = recs[0]
        py = " ".join(s.split()[0] for s in py.split())
        syl = py.split()
        cands = tone_cands(w)
        final = []
        for s, cs in zip(syl, cands):
            s = norm(s)
            hit = [c for c in cs if bare(c) == s]
            final.append(hit[0] if hit else cs[0])
        final = fix_syllables(w, final)
        rows.append({"w": w, "py": " ".join(final), "cnt": len({r[1] for r in recs}),
                     "dl": meta[did]["downloads"], "len": len(w)})
    print("新增", len(rows), "与既有重复", dup, "过滤", dict(skip))

    dist = Counter()
    for r in rows:
        base = 400 + 38 * min(r["cnt"], 5)
        if r["cnt"] > 5:
            base += 10 * (r["cnt"] - 5)
        if r["dl"] >= 1000000:
            base += 90
        elif r["dl"] >= 100000:
            base += 75
        elif r["dl"] >= 50000:
            base += 60
        elif r["dl"] >= 10000:
            base += 45
        elif r["dl"] >= 5000:
            base += 30
        elif r["dl"] >= 1000:
            base += 12
        if r["len"] == 2:
            base += 30
        elif r["len"] == 3:
            base += 15
        elif r["len"] >= 9:
            base -= 6 * (r["len"] - 8)
        r["freq"] = max(300, min(950, base // 5 * 5))
        dist[r["freq"]] += 1
    print("词频档", sorted(dist.items(), reverse=True)[:12])
    print("档位数", len(dist), "最高", max(dist), "最低", min(dist))
    rows.sort(key=lambda r: (-r["freq"], r["py"], r["w"]))
    (WORK / "rows.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    for r in rows[:5]:
        print(r)


if __name__ == "__main__":
    main()
