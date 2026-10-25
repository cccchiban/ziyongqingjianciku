# -*- coding: utf-8 -*-
"""把 2026 新番词条并入 动漫/更新.tsv（保留 2025 已有条目）。

`更新.tsv` 是「近年新番」合并库，2025 与 2026 混在一个文件里，按年份无法从
词面本身区分，故用 `kinds_2025.json` 记 2025 类型、`kinds_2026.json` 记 2026 类型，
写出时合成 `kinds_update.json`。

词源（与 2025 版一致）：
1. 作品名：维基「2026年日本动画列表」四季表格 → 312 词面
2. 角色名：各作品维基条目「登场人物」→ 抽取规则见 04_extract_chars.py
拼音用 pypinyin 词组读音；词频按可打性分档，2026 与 2025 同档（同为近年新番）。
"""
import io
import json
import pathlib
import re
import sys
from importlib import util

from pypinyin import Style, pinyin

HERE = pathlib.Path(__file__).parent
WORK = HERE.parent / ".omnicrawl_work"
REPO = HERE.parent.parent.parent

CJK = re.compile(u"[\\u3400-\\u9fff]")
NON_SYL = re.compile(u"[^\\u3400-\\u9fff]")
NORM = {"lue": "lve", "lue4": "lve4", "nue": "nve", "nue4": "nve4"}

WORD_FIX = {
    u"武藏": "wu3 zang4",
    u"判处勇者刑": "pan4 chu3 yong3 zhe3 xing2",
    u"泛而不精": "fan4 er2 bu4 jing1",
    u"幻想水浒传": "huan4 xiang3 shui3 hu3 zhuan4",   # 水浒传 zhuàn，非 chuán
    u"乱马1/2": "luan4 ma3 er4 fen1 zhi1 yi1",        # 1/2 读「二分之一」
}

STOP = frozenset(u"""偶像 先帝 内战 医官 医师 国王 皇帝 圣女 魔王 勇者 公主 王子 骑士
巫女 修女 女神 天使 恶魔 村民 商人 村长 队长 会长 社长 部长 科长 校长 老师 学生
主人 管家 女仆 执事 保镖 警察 医生 护士 记者 歌手 演员 画家 作家 诗人 侦探 犯人
父亲 母亲 姐姐 妹妹 哥哥 弟弟 祖父 祖母 爷爷 奶奶 女儿 儿子 妻子 丈夫 恋人
旁白 解说 主角 主人公 路人 敌人 同伴 对手 姐姐大人 哥哥大人 大小姐 大少爷
吟游诗人 圣骑士 魔法师 炼金术师 召唤师 冒险者 怪物 魔兽 精灵 矮人 巨人 龙族
刑务官 看守 囚犯 处刑人 惩罚勇者 队长大人 副队长""".split())

MIN_LEN = 2
MAX_LEN = 24
# 2025 季与 2026 季同为新番，词频不分年降档；季度先后只影响同年前后
SEASON_STEP = 15


def norm(s):
    return NORM.get(s, s)


# 词面里的数字要按其汉语读法取音，否则剥掉数字后音节数虽与汉字数相符、
# 格式校验能过，但用户敲 `ling2 wei4` 匹配不到 `从0位`。
DIGIT = {u"0": u"零", u"1": u"一", u"2": u"二", u"3": u"三", u"4": u"四",
         u"5": u"五", u"6": u"六", u"7": u"七", u"8": u"八", u"9": u"九"}


def digits_to_han(word):
    """把词面里的数字串替换成汉语读法（`100` → `一百`，`0` → `零`）。"""
    def rep(m):
        s = m.group(0)
        if s == u"0":
            return u"零"
        n = int(s)
        if n < 10:
            return DIGIT[s]
        if n < 20:
            return u"十" + (DIGIT[str(n % 10)] if n % 10 else u"")
        if n < 100:
            return DIGIT[str(n // 10)] + u"十" + (DIGIT[str(n % 10)] if n % 10 else u"")
        if n < 1000:
            h, r = divmod(n, 100)
            out = DIGIT[str(h)] + u"百"
            if r == 0:
                return out
            if r < 10:
                return out + u"零" + DIGIT[str(r)]
            t, u_ = divmod(r, 10)
            return out + DIGIT[str(t)] + u"十" + (DIGIT[str(u_)] if u_ else u"")
        return u"".join(DIGIT[c] for c in s)
    return re.sub(u"[0-9]+", rep, word)


def py_of(word):
    if word in WORD_FIX:
        return WORD_FIX[word]
    han = NON_SYL.sub("", digits_to_han(word))
    if not han:
        return None
    out = []
    for x in pinyin(han, style=Style.TONE3, neutral_tone_with_five=True):
        if not x:
            return None
        out.append(norm(x[0]))
    return " ".join(out)


def work_freq(w, tier):
    """作品名：按可打性分档，越短越易打，词频越高。"""
    n = len(w)
    if n <= 4:
        base = 860
    elif n <= 7:
        base = 830
    elif n <= 11:
        base = 800
    elif n <= 16:
        base = 770
    else:
        base = 740
    return max(300, min(900, base - SEASON_STEP * tier))


def char_freq(w, cnt, qj):
    """角色名：整体低于作品名一档；职称当角色名的压到 650。"""
    base = 650 + 10 * min(cnt, 6)
    if w in qj:
        base = min(base, 650)
    return max(300, min(760, base))


def main():
    names = json.load(open(WORK / "names_2026.json", encoding="utf-8"))
    spec = util.spec_from_file_location("x4", str(HERE.parent / "2025" / "04_extract_chars.py"))
    x4 = util.module_from_spec(spec)
    spec.loader.exec_module(x4)

    qj = {}
    for line in (REPO / "综合词库.qj").open(encoding="utf-8", errors="ignore"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3 and parts[0]:
            qj[parts[0]] = int(parts[2])

    # 既有 更新.tsv（2025 条目），保留原词频
    old = {}
    old_tsv = HERE.parent.parent / u"更新.tsv"
    for line in old_tsv.open(encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3 and parts[0]:
            # 2025 年那轮把词面里的数字与拉丁字母整段剥掉后取音，`2200年猫之国日本`
            # 只剩 `年猫之国日本` 的音、`Season4` 的 4 也被丢掉，用户敲数字匹配不到。
            # 这里按新逻辑（数字转汉语读法）重算拼音，词频沿用原值。
            py = py_of(parts[0])
            old[parts[0]] = (py or parts[1], int(parts[2]))
    old_kind = {r["w"]: r["kind"] for r in
                json.load(open(WORK / "kinds_2025.json", encoding="utf-8"))}
    print(u"既有 更新.tsv %d 条（2025）" % len(old))

    # 1) 2026 作品名
    works = {}
    for q, tier in [(u"冬", 0), (u"春", 1), (u"夏", 2), (u"秋", 3)]:
        # 同一 src 的第 1 个词面是正式主名，其后是切出的派生片段（`草莓哀歌`、
        # `北斗之拳`），片段降 45 分，避免压过正式名
        first_of = {}
        for r in names[q]:
            first_of.setdefault(r["src"], r["w"])
        for r in names[q]:
            w = r["w"].strip()
            if len(w) < MIN_LEN or len(w) > MAX_LEN or not CJK.search(w):
                continue
            deriv = w != first_of.get(r["src"])
            works.setdefault(w, (tier, deriv))

    # 2) 2026 角色名
    raw = WORK / "char_raw"
    chars = {}
    for p in sorted(raw.glob("*.txt")):
        if p.stat().st_size <= 1024:
            continue
        for n, _jp in x4.extract(p.read_text(encoding="utf-8")):
            n = n.strip()
            if len(n) < MIN_LEN or not CJK.search(n) or n in STOP:
                continue
            chars[n] = chars.get(n, 0) + 1
    print(u"2026 作品名词面 %d，角色名 %d" % (len(works), len(chars)))

    out = dict(old)
    kinds = dict(old_kind)
    added = 0
    for w, (tier, deriv) in works.items():
        if w in out:
            continue
        f = work_freq(w, tier)
        if deriv:
            f = max(300, f - 45)
        py = py_of(w)
        if not py or w not in WORD_FIX and len(py.split()) != len(
                NON_SYL.sub("", digits_to_han(w))):
            continue
        out[w] = (py, f)
        kinds[w] = u"作品"
        added += 1
    for w, cnt in chars.items():
        if w in out or w in works:
            continue
        py = py_of(w)
        if not py or w not in WORD_FIX and len(py.split()) != len(
                NON_SYL.sub("", digits_to_han(w))):
            continue
        out[w] = (py, char_freq(w, cnt, qj))
        kinds[w] = u"角色"
        added += 1
    print(u"2026 新增 %d 条，合并后 %d 条" % (added, len(out)))

    rows = sorted(((w, py, f) for w, (py, f) in out.items()),
                  key=lambda r: (-r[2], r[1], r[0]))
    with io.open(old_tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write(u"\n".join(u"%s\t%s\t%d" % r for r in rows) + u"\n")
    print(u"写出 %s：%d 条" % (old_tsv.name, len(rows)))

    json.dump([{"w": w, "kind": kinds.get(w, u"角色")} for w, _p, _f in rows],
              io.open(WORK / "kinds_update.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
