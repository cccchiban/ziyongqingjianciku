# -*- coding: utf-8 -*-
"""把维基提取的 253 部作品名规范化成可输入的词库词条。

维基作品名多为「正式全名 + 季别括注」，如：
    我独自升级 第二季 -起于暗影-（第2期）
    青之驱魔师 终夜篇（第5期）
    地缚少年花子君2（第2期上半）
输入法里用户打的是 `我独自升级`、`青之驱魔师`、`地缚少年花子君`，
故剥掉季别/期数括注与副标题，得到主名；副标题单独成条（若有意义）。
"""
import json
import pathlib
import re
import sys

WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
SRC = WORK / "wiki_2025.json"
OUT = WORK / "names_2025.json"

# 季别括注：（第2期）（第3期上半）（上半）（下半）（第2期）-（最終季）等
SEASON_PAREN = re.compile(u"[（(][^（()）]*(第[0-9一二三四五六七八九十]+[期季部]"
                          u"|[上中下]半|最終季|最终季|Season ?\\d+)[^（()）]*[）)]", re.I)
# 尾部季别短语：第二季 / 第2期 / Season 2 / 3rd season / 剧场版
SEASON_TAIL = re.compile(u"\\s*[-－—～~·]*\\s*(第[0-9一二三四五六七八九十]+[季期部]"
                         u"|Season ?\\d+|\\d+(st|nd|rd|th) ?season"
                         u"|剧场版|劇場版)\\s*$", re.I)
# 尾部副标题：以空格或破折号隔开的后半段（仅当主名 >= 3 字时剥）
DASH_TAIL = re.compile(u"\\s*[-－—]+\\s*[^-－—]+$")
# 结尾标点
TAIL_PUNCT = re.compile(u"[。！？!?、，,\\s]+$")
LATIN = re.compile(u"[A-Za-z]")


def variants(zh):
    """产出一个作品的可输入词面集合（含主名与副标题）。"""
    out = []
    s = zh.strip()

    # 1) 剥季别括注（可能多个）
    for _ in range(3):
        s2 = SEASON_PAREN.sub("", s)
        if s2 == s:
            break
        s = s2
    s = TAIL_PUNCT.sub("", s.strip())
    if s:
        out.append(s)

    # 2) 剥尾部季别短语
    s3 = SEASON_TAIL.sub("", s)
    s3 = TAIL_PUNCT.sub("", s3.strip())
    if s3 and s3 != s:
        out.append(s3)

    # 3) 剥破折号副标题（主名 >= 3 字才剥，避免 `Re:从零开始` 被切坏）
    base = s3 or s
    m = DASH_TAIL.search(base)
    if m and len(base[:m.start()].strip()) >= 3:
        out.append(base[:m.start()].strip())

    # 4) 长标题按空格切出前段（>=4 字）——仅对**全中文**标题，含拉丁字母的
    #    标题不能这样切：`MOMENTARY LILY 刹那之花` 会被切成 MOMENTARY、
    #    `卡片战斗!! 先导者 Divinez` 会被切成 `卡片战斗!!`、`～MIRAI DAYS～`
    #    会被切成 `～MIRAI`，全是残片。
    for cand in list(out):
        if len(cand) >= 14 and " " in cand and not LATIN.search(cand):
            head = cand.split(" ")[0].strip()
            if len(head) >= 4:
                out.append(head)

    # 5) 超长标题取「首个自然停点」之前的核心名。输入法里用户不会打 40 字全名，
    #    实际打的是 `持续狩猎史莱姆三百年`、`Re:从零开始的异世界生活`、
    #    `魔法少女小圆`、`卡片战斗` 这类前缀。停点取逗号/波浪号/空格/书名号。
    for cand in list(out):
        if len(cand) >= 22:
            m = re.search(u"[，,～~／/〈《「『！!？?。．]|\\s", cand)
            if m and m.start() >= 4:
                out.append(cand[:m.start()].strip())

    # 6) 含书名号的，书名号内内容也单独成条（`〈魔法少女小圆：起始的物语／…〉`）
    for cand in list(out):
        for inner in re.findall(u"[《〈「『]([^》〉」』]{2,20})[》〉」』]", cand):
            out.append(inner)

    res = []
    for c in out:
        c = c.strip(" 　〜～~")
        if not c:
            continue
        if len(c) < 2:
            continue
        res.append(c)
    return res


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    res = {}
    for q, items in data.items():
        rows = []
        for it in items:
            for v in variants(it["zh"]):
                rows.append({"w": v, "src": it["zh"], "date": it["date"]})
        # 去重，保留首次
        seen, uniq = set(), []
        for r in rows:
            if r["w"] not in seen:
                seen.add(r["w"])
                uniq.append(r)
        res[q] = uniq
        print(u"%s季 %d 部 → %d 个词面" % (q, len(items), len(uniq)))
    allw = {r["w"] for v in res.values() for r in v}
    print(u"合计 %d 个唯一词面" % len(allw))
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    print(u"\n=== 抽样：原文 → 词面 ===")
    shown = 0
    for q in [u"冬", u"春"]:
        for r in res[q]:
            if r["w"] != r["src"] and shown < 26:
                print(u"  %-46s → %s" % (r["src"], r["w"]))
                shown += 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
