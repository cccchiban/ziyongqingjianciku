# -*- coding: utf-8 -*-
"""生成 动漫/更新.tsv：2025 年新番词库。

词源两类：
1. 作品名：维基「2025年日本动画列表」四季表格（253 部 → 289 个词面）。
2. 角色名：各作品维基条目的「登场人物」角色表（174 部抓到 → 1416 个角色名）。

拼音用 pypinyin 词组读音（与 `动漫词库.tsv` 同一策略，实测与综合库吻合 98.2%），
词频按词条类型分档：作品名高于角色名，角色名高于边缘词。

判重：与既有源词库判重的规则同 `动漫词库`——排除派生文件与语料型大库，
避免 `更新.tsv` 自我判重。
"""
import io
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from importlib import util

from pypinyin import Style, pinyin

HERE = pathlib.Path(__file__).parent
WORK = HERE.parent / ".omnicrawl_work"
REPO = HERE.parent.parent.parent

CJK = re.compile(u"[\\u3400-\\u9fff]")
# 拼音只能由音节组成：词面里的标点、书名号、拉丁字母不进拼音。
# pypinyin 会把 `《`、`，`、`（`、`～`、`【` 原样当「音节」返回，直接拼进
# 第三字段就成了 `《 bei4 xi1 mo1 si1 》` 这种不可用的脏拼音。
NON_SYL = re.compile(u"[^\\u3400-\\u9fff]")
NORM = {"lue": "lve", "lue4": "lve4", "nue": "nve", "nue4": "nve4"}

# 词级读音修正：pypinyin 按常用义猜错的专名，仅收能确定通行读法的
WORD_FIX = {
    u"武藏": "wu3 zang4",
    u"刹那之花": "cha4 na4 zhi1 hua1",
    u"全修": "quan2 xiu1",
    u"地缚少年花子君": "di4 fu4 shao4 nian2 hua1 zi5 jun1",
}

# 角色名里混进的通用词/身份词，被收录会挤掉日常候选（`偶像`、`内战`、`医师`）
STOP = frozenset(u"""偶像 先帝 内战 医官 医师 国王 皇帝 圣女 魔王 勇者 公主 王子 骑士
巫女 修女 女神 天使 恶魔 村民 商人 村长 队长 会长 社长 部长 科长 校长 老师 学生
主人 管家 女仆 执事 保镖 警察 医生 护士 记者 歌手 演员 画家 作家 诗人 侦探 犯人
父亲 母亲 姐姐 妹妹 哥哥 弟弟 祖父 祖母 爷爷 奶奶 女儿 儿子 妻子 丈夫 恋人
旁白 解说 主角 主人公 路人 敌人 同伴 对手 姐姐大人 哥哥大人 大小姐 大少爷
不死 云端 冰火 四季 迷雾 千手 双叶 和田 田中 松田 山田 佐藤 铃木 高桥 渡边
吟游诗人 圣骑士 魔法师 炼金术师 召唤师 冒险者 怪物 魔兽 精灵 矮人 巨人 龙族""".split())

# 单字名（`凛`、`零`）与过短词面不收录：输入时无区分度
MIN_LEN = 2
# 超过此长度的作品名作为词条没有输入价值：用户在输入法里不会打 40 字全名，
# 长标题已在 02_normalize.py 里抽出核心短名（如 `差点在迷宫深处被信任的伙伴杀掉`
# 之外还有 `持续狩猎史莱姆三百年`）。这里只挡住剩余的完整长名。
MAX_LEN = 24


def norm(s):
    return NORM.get(s, s)


def py_of(word):
    """只对汉字取音，词面里的标点与字母跳过，保证音节数 == 汉字数。"""
    if word in WORD_FIX:
        return WORD_FIX[word]
    han = NON_SYL.sub("", word)
    if not han:
        return None
    out = []
    for x in pinyin(han, style=Style.TONE3, neutral_tone_with_five=True):
        if not x:
            return None
        out.append(norm(x[0]))
    return " ".join(out)


def existing_words():
    skip = {"综合词库.qj", "综合词库.tsv", "游戏/游戏词库合集.qj",
            "文学作品/文学作品词库.tsv", "动漫/动漫词库.tsv", "动漫/更新.tsv"}
    words = set()
    for pat in ("*.tsv", "*.qj", "*/*.tsv", "*/*.qj", "*/*/*.tsv", "*/*/*.qj"):
        for p in REPO.glob(pat):
            rel = p.relative_to(REPO).as_posix()
            if rel in skip or rel.startswith(".omnicrawl"):
                continue
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                w = line.split("\t")[0].strip()
                if w:
                    words.add(w)
    return words


def main():
    names = json.load(open(WORK / "names_2025.json", encoding="utf-8"))
    spec = util.spec_from_file_location("x4", str(HERE / "04_extract_chars.py"))
    x4 = util.module_from_spec(spec)
    spec.loader.exec_module(x4)

    # 1) 作品名词面：按季度先后给档（越晚的季度越新、曝光越少）。
    #    同一 src 的第 1 个词面是正式主名，其后的词面是从书名号/空格/破折号
    #    切出的派生片段（`S级怪兽`、`贝希摩斯` 之于
    #    `S级怪兽《贝希摩斯》被误认成小猫…`）。片段仍收录——用户确实会只打
    #    `贝希摩斯`——但要降档，不能让片段压过正式作品名。
    works = {}
    for q, tier in [(u"冬", 0), (u"春", 1), (u"夏", 2), (u"秋", 3)]:
        seen_src = set()
        for r in names[q]:
            src = r["src"]
            primary = src not in seen_src
            seen_src.add(src)
            w = r["w"].strip()
            if len(w) < MIN_LEN or len(w) > MAX_LEN or not CJK.search(w):
                continue
            t = tier + (0 if primary else 4)
            if w not in works or works[w] > t:
                works[w] = t

    # 2) 角色名
    raw = HERE.parent / ".omnicrawl_work" / "char_raw"
    chars = {}
    for p in sorted(raw.glob("*.txt")):
        if p.stat().st_size <= 1024:
            continue
        for n, _jp in x4.extract(p.read_text(encoding="utf-8")):
            n = n.strip()
            if len(n) < MIN_LEN or len(n) > MAX_LEN or not CJK.search(n) or n in STOP:
                continue
            chars[n] = chars.get(n, 0) + 1

    exist = existing_words()
    print(u"作品名词面 %d，角色名 %d，判重集 %d" % (len(works), len(chars), len(exist)))

    # 词频按「词条在输入法里的可打性」分档，而不是按长度：
    # 短名（`胆大党`、`摩绪`）比 24 字全名（`离开A级队伍的我，和从前的弟子往
    # 迷宫深处迈进`）更可能被打出，故短名在上。季度越晚曝光越少，再降一档。
    rows, dup = [], 0
    for w, tier in works.items():
        if w in exist:
            dup += 1
            continue
        if len(w) <= 4:
            base = 860
        elif len(w) <= 7:
            base = 830
        elif len(w) <= 11:
            base = 800
        elif len(w) <= 16:
            base = 770
        else:
            base = 740
        base -= 15 * min(tier, 3)
        base -= 45 if tier >= 4 else 0      # 派生片段整体降一档
        rows.append({"w": w, "freq": max(300, base), "kind": u"作品"})
    for w, cnt in chars.items():
        if w in exist or w in works:
            if w in exist:
                dup += 1
            continue
        # 角色名整体低于作品名一档：用户先想作品再想角色，且角色名数量多、
        # 单条区分度低。被多部作品同时收录的（cnt 大）说明是常青角色，略提。
        if len(w) <= 3:
            base = 700
        elif len(w) <= 5:
            base = 675
        else:
            base = 650
        base += 10 * min(cnt, 6)
        rows.append({"w": w, "freq": max(300, min(760, base)), "kind": u"角色"})
    print(u"入库 %d（作品 %d、角色 %d），与既有库重复 %d"
          % (len(rows), sum(1 for r in rows if r["kind"] == u"作品"),
             sum(1 for r in rows if r["kind"] == u"角色"), dup))

    out, bad = [], 0
    for r in rows:
        py = py_of(r["w"])
        han = NON_SYL.sub("", r["w"])
        if not py or not han or len(py.split()) != len(han):
            bad += 1
            continue
        out.append((r["w"], py, r["freq"], r["kind"]))
    print(u"拼音异常剔除 %d" % bad)

    out.sort(key=lambda x: (-x[2], x[1], x[0]))
    lines = ["%s\t%s\t%d" % (w, py, f) for w, py, f, _k in out]
    dest = HERE.parent.parent / u"更新.tsv"
    with io.open(dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(u"\n".join(lines) + u"\n")
    print(u"写出 %s：%d 条" % (dest.name, len(out)))

    json.dump([{"w": w, "kind": k} for w, _p, _f, k in out],
              io.open(WORK / "kinds_2025.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for w, py, f, k in out[:12]:
        print(u"  %-24s %-32s %4d %s" % (w, py, f, k))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
