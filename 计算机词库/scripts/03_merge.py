"""合并 233 个 scel：整库排除语料型 → 按词面去重 → 与既有源词库判重 → 合成拼音与词频。"""
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
# 企业名与「译名A译名B」式的词典释义拼接，不是可输入词条
ORG = re.compile(u"(有限公司|股份公司|股份有限公司|有限责任公司|集团)$")
def glued(word):
    """词典把两个译名并列写成一条（…语法…语法），不是可输入词条。"""
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


def chatty(word):
    """对话句与口语化吧名，不是术语。"""
    if word.startswith((u"请您", u"请插", u"请将", u"请按", u"请点", u"请选择", u"请检查",
                        u"请确认", u"请稍", u"请重", u"请先", u"请关", u"请输", u"请使用")):
        return True
    return word[-1] in u"吧吗呢"


FUNC = set("的了是我您你吗呢吧啊在和与就都也很把被让给对从到以及并或者这那些个请麻烦谢谢")

# 整库排除：句子、话术、工单、提示词指令，或企业/个人自建词库（内容为公司名与人名）
EXCLUDE_NAMES = [
    u"项目经理案头手册", u"360电脑专家话术", u"机场专业用词", u"蚂蚁云客服-花呗云",
    u"铁塔电信运维故障工单专用词汇", u"角色t83", u"百度术语词条（文学类）", u"牛皮癣标题",
    u"焙烧煤矸石、", u"工作词汇添加", u"行测", u"会计考试用", u"协会", u"甘肃小青年",
    u"百草软件", u"致立方", u"董雅斯", u"覃澜", u"中周动力", u"火迅网络科技", u"北诚",
    u"九洲云网", u"渲云", u"火迅网络", u"速享校园", u"巨蘑菇", u"信析宝", u"纳宝科技",
    u"炫控网络", u"教之初", u"镜玩", u"爱特联", u"速享科技", u"房蚁", u"简鸽", u"青亭",
    u"掌界", u"彬创网络", u"爱赫赫", u"奇尚数据", u"世信", u"虎窝", u"星际魔方",
    u"南京吉印", u"凡科", u"万得网络科技", u"茗鹤云", u"钛投标", u"拣券", u"优恪词库",
    u"脉客大师", u"球路坦途公司词库", u"蓝视云网络LSHIYNetwork",
    u"沈阳皮克趣网络科技有限公司", u"河北网新科技集团有限公司", u"河南万亿宝网络科技有限公司",
    u"物联网教学设备厂家", u"宜播多机位直播软件", u"深圳龙腾图书馆管理软件系统", u"爱采集大师",
    u"工作词汇添加",
]

SINGLE = {
    "重": ["chong2", "zhong4"], "调": ["tiao2", "diao4"], "长": ["chang2", "zhang3"],
    "识": ["zhi4", "shi2"], "行": ["hang2", "xing2"], "钥": ["yue4", "yao4"],
    "似": ["si4", "shi4"], "校": ["jiao4", "xiao4"], "模": ["mu2", "mo2"],
    "弹": ["tan2", "dan4"], "塞": ["se4", "sai1"], "的": ["di4", "de5"],
    "称": ["chen4", "cheng1"], "着": ["zhao2", "zhuo2", "zhe5"], "乐": ["yue4", "le4"],
    "还": ["huan2", "hai2"], "地": ["de5", "di4"], "角": ["jue2", "jiao3"],
    "栅": ["shan1", "zha4"], "会": ["kuai4", "hui4"], "奇": ["ji1", "qi2"],
    "露": ["lou4", "lu4"], "薄": ["bo2", "bao2"], "伺": ["si4", "ci4"],
    "了": ["liao3", "le5"], "勒": ["le4", "lei1"], "色": ["shai3", "se4"],
    "粘": ["nian2", "zhan1"], "都": ["du1", "dou1"], "差": ["chai1", "ci1", "cha4"],
    "曝": ["bao4", "pu4"], "晟": ["sheng4", "cheng2"], "劲": ["jing4", "jin4"],
    "佛": ["fo2", "fu2"], "省": ["xing3", "sheng3"], "属": ["zhu3", "shu3"],
    "没": ["mo4", "mei2"], "给": ["ji3", "gei3"], "壳": ["qiao4", "ke2"],
    "传": ["zhuan4", "chuan2"], "便": ["pian2", "bian4"], "什": ["shi2", "shen2"],
    "隽": ["jun4", "juan4"], "泊": ["bo2", "po1"], "熟": ["shou2", "shu2"],
    "恶": ["wu4", "e4"], "掺": ["chan1", "can4"], "啁": ["zhou1", "zhao1"],
    "柏": ["bo2", "bai3"], "迫": ["pai3", "po4"], "囤": ["tun2", "dun4"],
    "卡": ["qia3", "ka3"], "攒": ["cuan2", "zan3"], "落": ["lao4", "luo4"],
    "率": ["shuai4", "lv4"], "这": ["zhei4", "zhe4"], "仔": ["zi3", "zai3"],
    "扎": ["za1", "zha1"], "藏": ["zang4", "cang2"], "戲": ["hu1", "xi4"],
    "龟": ["jun1", "gui1"], "伽": ["jia1", "ga1"], "吁": ["yu4", "xu1"],
    "卜": ["bu3", "bo5"], "茄": ["qie2", "jia1"], "琢": ["zhuo2", "zuo2"],
    "和": ["huo4", "he2"], "忒": ["tei1", "te4"], "吓": ["he4", "xia4"],
    "解": ["xie4", "jie3"], "靓": ["liang4", "jing4"], "单": ["shan4", "dan1"],
    "参": ["cen1", "can1"], "唛": ["mai4", "ma4"], "肋": ["lei4", "le1"],
    "覃": ["qin2", "tan2"], "兹": ["ci2", "zi1"], "纤": ["qian4", "xian1"],
    "匙": ["chi2", "shi5"], "削": ["xiao1", "xue1"], "蚌": ["beng4", "bang4"],
    "龈": ["yin2", "ken3"],
}
NORM = {"lue": "lve", "lue4": "lve4", "nue": "nve", "nue4": "nve4"}

# 通行读音，纠正 scel 源标注的多音字错误（校验/校正 读 jiao4 是正确的，不在此列）
SYL_FIX = {
    "识": {"zhi": "shi2"},   # 标识 biao1 shi2，不是 biao1 zhi4
    "钥": {"yue": "yao4"},   # 密钥 mi4 yao4
}

# 词级读音修正：源库把「重新做一次」的「重」标成 zhong4
WORD_FIX = {
    "重配置": "chong2 pei4 zhi4",
    "重定时": "chong2 ding4 shi2",
    "重定时变换": "chong2 ding4 shi2 bian4 huan4",
    "重采样": "chong2 cai3 yang4",
    "重配置管理": "chong2 pei4 zhi4 guan3 li3",
    "可重配置": "ke3 chong2 pei4 zhi4",
    "动态重配置": "dong4 tai4 chong2 pei4 zhi4",
}


def fix_syllables(word, syllables):
    if word in WORD_FIX:
        return WORD_FIX[word].split()
    out = []
    for ch, s in zip(word, syllables):
        s = norm(s)
        out.append(SYL_FIX.get(ch, {}).get(bare(s), s))
    return out


def norm(s):
    s = s.replace("ü", "v")
    return NORM.get(s, s)


def bare(s):
    return norm("".join(c for c in s if not c.isdigit()))


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


def existing_words():
    skip = {"综合词库.qj", "游戏/游戏词库合集.qj"}
    words = set()
    for pat in ("*.tsv", "*.qj", "*/*.tsv", "*/*.qj"):
        for p in REPO.glob(pat):
            rel = p.relative_to(REPO).as_posix()
            if rel in skip or rel.startswith(".omnicrawl") or rel.startswith("计算机词库"):
                continue
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                w = line.split("\t")[0].strip()
                if w:
                    words.add(w)
    return words


def main():
    meta = {m["id"]: m for m in json.load(open(WORK / "meta.json", encoding="utf-8"))}
    excluded = {m["id"] for m in meta.values() if m["name"] in EXCLUDE_NAMES}
    print("整库排除", len(excluded), "个")
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
    rows, dup = [], 0
    for w, recs in cand.items():
        if w in exist:
            dup += 1
            continue
        pick = recs[0]
        py, did = pick[0], pick[1]
        if glued(w) or chatty(w):
            continue
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
    print("新增", len(rows), "与既有重复", dup)

    dist = Counter()
    for r in rows:
        # 共现库数（1—10）贡献 0—170，源库下载量贡献 0—90，词长做微调
        base = 400 + 38 * min(r["cnt"], 5)
        if r["cnt"] > 5:
            base += 10 * (r["cnt"] - 5)
        if r["dl"] >= 1000000:
            base += 90
        elif r["dl"] >= 500000:
            base += 70
        elif r["dl"] >= 50000:
            base += 50
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
    print("词频档", sorted(dist.items(), reverse=True)[:14])
    print("档位数", len(dist), "最高", max(dist), "最低", min(dist))
    rows.sort(key=lambda r: (-r["freq"], r["py"], r["w"]))
    (WORK / "rows.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    for r in rows[:5]:
        print(r)


if __name__ == "__main__":
    main()
