# -*- coding: utf-8 -*-
"""把 2026 年作品名规范化成可输入词面。

逻辑与 `../2025/02_normalize.py` 一致，仅输入输出文件不同：
维基作品名多为「正式全名 + 季别括注」，如
    正义使者 -我的英雄学院之非法英雄-（第2期）
    北斗之拳 拳王军杂兵们的挽歌（上半）
输入法里打的是主名，故剥掉季别/期数括注与副标题；副标题单独成条。
输出 .omnicrawl_work/names_2026.json。
"""
import json
import pathlib
import re
import sys

WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
SRC = WORK / "wiki_2026.json"
OUT = WORK / "names_2026.json"

SEASON_PAREN = re.compile(u"[（(][^（()）]*(第[0-9一二三四五六七八九十]+[期季部]"
                          u"|[上中下]半|最終季|最终季|Season ?\\d+)[^（()）]*[）)]", re.I)
SEASON_TAIL = re.compile(u"\\s*[-－—～~·]*\\s*(第[0-9一二三四五六七八九十]+[季期部]"
                         u"|Season ?\\d+|\\d+(st|nd|rd|th) ?season"
                         u"|剧场版|劇場版)\\s*$", re.I)
DASH_TAIL = re.compile(u"\\s*[-－—]+\\s*[^-－—]+$")
TAIL_PUNCT = re.compile(u"[。！？!?、，,\\s]+$")
LATIN = re.compile(u"[A-Za-z]")


def variants(zh):
    out = []
    s = zh.strip()
    for _ in range(3):
        s2 = SEASON_PAREN.sub("", s)
        if s2 == s:
            break
        s = s2
    s = TAIL_PUNCT.sub("", s.strip())
    if s:
        out.append(s)

    s3 = SEASON_TAIL.sub("", s)
    s3 = TAIL_PUNCT.sub("", s3.strip())
    if s3 and s3 != s:
        out.append(s3)

    base = s3 or s
    m = DASH_TAIL.search(base)
    if m and len(base[:m.start()].strip()) >= 3:
        out.append(base[:m.start()].strip())

    # 长标题按空格切前段，仅限全中文（含拉丁字母的不能切，会切出残片）
    for cand in list(out):
        if len(cand) >= 14 and " " in cand and not LATIN.search(cand):
            head = cand.split(" ")[0].strip()
            if len(head) >= 4:
                out.append(head)

    # 超长标题取「首个自然停点」前的核心名
    for cand in list(out):
        if len(cand) >= 22:
            m2 = re.search(u"[，,～~／/〈《「『！!？?。．]|\\s", cand)
            if m2 and m2.start() >= 4:
                out.append(cand[:m2.start()].strip())

    # 书名号内内容单独成条
    for cand in list(out):
        for inner in re.findall(u"[《〈「『]([^》〉」』]{2,20})[》〉」』]", cand):
            out.append(inner)

    res = []
    for c in out:
        c = c.strip(u" 　〜～~")
        if c and len(c) >= 2:
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
            if r["w"] != r["src"] and shown < 24:
                print(u"  %-46s → %s" % (r["src"], r["w"]))
                shown += 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
