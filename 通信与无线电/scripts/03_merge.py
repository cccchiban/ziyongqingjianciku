"""合并 16 个通信与无线电 scel：整库排除 → 词面去重 → 与既有源库判重 → 合成拼音与词频。"""
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
ORG = re.compile(u"(有限公司|股份公司|股份有限公司|有限责任公司|集团|分公司)$")

# 整库排除：与通信无关的地名库、工单记录
EXCLUDE_NAMES = [
    u"上海站名XX",           # 44815 条上海小区与站点名（阿波罗大厦、爱博二村地下车库）
    u"通信代维运营商-伍",     # 6 条工单事件描述（客服报障、合同物业纠纷）
]

SINGLE = {
    "重": ["chong2", "zhong4"], "调": ["tiao2", "diao4"], "长": ["chang2", "zhang3"],
    "行": ["hang2", "xing2"], "模": ["mu2", "mo2"], "弹": ["tan2", "dan4"],
    "校": ["jiao4", "xiao4"], "识": ["zhi4", "shi2"], "率": ["shuai4", "lv4"],
    "轧": ["zha2", "ya4"], "扎": ["za1", "zha1"], "粘": ["nian2", "zhan1"],
    "称": ["chen4", "cheng1"], "着": ["zhuo2", "zhao2", "zhe5"], "薄": ["bo2", "bao2"],
    "栅": ["shan1", "zha4"], "壳": ["qiao4", "ke2"], "塞": ["se4", "sai1"],
    "剥": ["bao1", "bo1"], "削": ["xiao1", "xue1"], "勒": ["le4", "lei1"],
    "龟": ["jun1", "gui1"], "差": ["cha1", "chai1", "ci1"], "都": ["du1", "dou1"],
    "给": ["ji3", "gei3"], "露": ["lou4", "lu4"], "没": ["mo4", "mei2"],
    "还": ["huan2", "hai2"], "似": ["si4", "shi4"], "色": ["shai3", "se4"],
    "卡": ["qia3", "ka3"], "省": ["xing3", "sheng3"], "属": ["zhu3", "shu3"],
    "传": ["zhuan4", "chuan2"], "便": ["pian2", "bian4"], "什": ["shi2", "shen2"],
    "熟": ["shou2", "shu2"], "恶": ["wu4", "e4"], "柏": ["bo2", "bai3"],
    "迫": ["pai3", "po4"], "落": ["lao4", "luo4"], "仔": ["zi3", "zai3"],
    "藏": ["zang4", "cang2"], "和": ["huo4", "he2"], "解": ["xie4", "jie3"],
    "单": ["shan4", "dan1"], "参": ["cen1", "can1"], "纤": ["qian4", "xian1"],
    "匙": ["chi2", "shi5"], "钥": ["yue4", "yao4"], "了": ["liao3", "le5"],
    "奇": ["ji1", "qi2"], "会": ["kuai4", "hui4"], "角": ["jue2", "jiao3"],
    "曝": ["bao4", "pu4"], "勒": ["le4", "lei1"], "的": ["de5", "di4"],
    "子": ["zi3", "zi5"],
}
NORM = {"lue": "lve", "lue4": "lve4", "nue": "nve", "nue4": "nve4"}

# 术语里「子」一律读本调 zi3（端子、子网、子帧、子载波），不是轻声
SYL_FIX = {"子": {"zi": "zi3"}, "识": {"zhi": "shi2"}, "钥": {"yue": "yao4"}}


def norm(s):
    s = s.replace("ü", "v")
    return NORM.get(s, s)


def bare(s):
    return norm("".join(c for c in s if not c.isdigit()))


def fix_syllables(word, syllables):
    out = []
    for ch, s in zip(word, syllables):
        s = norm(s)
        out.append(SYL_FIX.get(ch, {}).get(bare(s), s))
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
    """词典把两个译名或两个术语并列写成一条。"""
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
    if word.startswith((u"请您", u"请插", u"请将", u"请按", u"请点", u"请选择", u"请检查",
                        u"请确认", u"请稍", u"请重", u"请先", u"请关", u"请输", u"请使用")):
        return True
    return word[-1] in u"吧吗呢"


# 工程表单行、设备清单行、营销套餐名，不是通信术语
JUNK = [
    u"工程过程文档资料目录表", u"督导阶段工程质量评估表", u"调测阶段工程质量评估表",
    u"工程服务满意度调查表", u"工程服务危险源识别登记表", u"已安装设备主材明细表",
    u"已安装工程量总表", u"综合机柜数码顺德房专用", u"芯配线柜独立单元寸机柜用",
    u"综合配线柜寸带穿线底座", u"芯双头熔配一体化单元世纪人", u"单端口信息插座含面板底盒",
    u"动感地带象牙塔劲爆套餐", u"动感地带音乐套餐", u"象牙塔劲爆套餐",
    u"综合信息服务门户增值产品介绍", u"局用数字程控交换机安装验收报告",
    u"局用数字程控交换机开通测试记录", u"功率控制级别等",
]
JUNK_SET = set(JUNK)


def existing_words():
    skip = {"综合词库.qj", "游戏/游戏词库合集.qj"}
    words = set()
    for pat in ("*.tsv", "*.qj", "*/*.tsv", "*/*.qj"):
        for p in REPO.glob(pat):
            rel = p.relative_to(REPO).as_posix()
            if rel in skip or rel.startswith(".omnicrawl") or rel.startswith("通信与无线电"):
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
        if w in JUNK_SET:
            skip["junk"] += 1
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
    print("词频档", sorted(dist.items(), reverse=True)[:10])
    print("档位数", len(dist), "最高", max(dist), "最低", min(dist))
    rows.sort(key=lambda r: (-r["freq"], r["py"], r["w"]))
    (WORK / "rows.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    for r in rows[:5]:
        print(r)


if __name__ == "__main__":
    main()
