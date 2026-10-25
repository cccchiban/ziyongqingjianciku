# -*- coding: utf-8 -*-
"""从维基「2026年日本动画列表」提取电视动画的**中文作品名**。

逻辑与 `../01_parse_wiki.py`（2025 版）一致，仅年份与输出名不同：
原文结构（提取纯文本后为单行长串）
    季度标记 → 表头「开始日－结束日 作品名 原名 制作公司 话数 参考」
    → 每条「开始日 [－结束日] 中文名 日文原名 制作公司 N话 [脚注]」
词库只收中文词面：有假名片段时中文名 = 假名前文本；无假名时取第一个空格段。

输出 .omnicrawl_work/wiki_2026.json：{季: [{zh, date}]}
"""
import json
import pathlib
import re
import sys

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
    r"C:\Users\Administrator\.OmniCrawl\.agent_sessions\artifacts\20261025-073336-3cc59a\tool_result_adfe7a9262b9a06e.txt")
WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
WORK.mkdir(parents=True, exist_ok=True)

QUARTERS = [(u"1月－3月", u"冬"), (u"4月－6月", u"春"),
            (u"7月－9月", u"夏"), (u"10月－12月", u"秋")]
# 记录起点。排除跨年日期后半截（「10月1日－2027年1月28日」中的「1月28日」），
# 否则记录被切碎并产出「2027年」这类伪作品名。
HEAD = re.compile(u"(?<![\\d年])(\\d{1,2}月\\d{1,2}日)(\\[[^\\]]{1,8}\\])?")
KANA = re.compile(u"[ぁ-んァ-ヶー]")
CJK = re.compile(u"[\\u3400-\\u9fff]")


def zh_name(chunk):
    chunk = re.sub(u"\\[[^\\]]*\\]", " ", chunk)
    m = None
    for m in re.finditer(u"\\d+话", chunk):
        pass
    if m:
        chunk = chunk[:m.start()]
    chunk = chunk.strip().lstrip(u"－-–— ").strip()
    chunk = re.sub(u"^\\d{4}年\\d{1,2}月\\d{1,2}日\\s*", "", chunk)
    chunk = re.sub(u"^[－\\-–—]+\\s*", "", chunk)
    if not chunk:
        return None
    k = KANA.search(chunk)
    if k:
        i = k.start()
        j = chunk.rfind(" ", 0, i)
        name = chunk if j < 0 else chunk[:j]
    else:
        name = chunk.split()[0] if " " in chunk else chunk
    name = name.strip()
    if not name or not CJK.search(name):
        return None
    return name


def main():
    text = SRC.read_text(encoding="utf-8")
    marks = []
    for mk, lb in QUARTERS:
        i = text.find(mk)
        if i >= 0:
            marks.append((i, lb))
    marks.sort()

    res = {}
    for n, (i, label) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(text)
        seg = text[i:end]
        c = seg.find(u"注释")
        if c > 0:
            seg = seg[:c]
        body = seg[seg.find(u"参考") + 2:] if u"参考" in seg else seg
        heads = [m.start() for m in HEAD.finditer(body)]
        items, seen = [], set()
        for k, s in enumerate(heads):
            e = heads[k + 1] if k + 1 < len(heads) else len(body)
            chunk = body[s:e]
            dm = HEAD.match(chunk)
            date = dm.group(1) if dm else ""
            nm = zh_name(HEAD.sub("", chunk, count=1))
            if nm and nm not in seen:
                seen.add(nm)
                items.append({"zh": nm, "date": date})
        res[label] = items
        print(u"%s季 %d 部" % (label, len(items)))

    allz = [x["zh"] for v in res.values() for x in v]
    print(u"合计 %d 部，去重后 %d 部" % (len(allz), len(set(allz))))
    WORK.joinpath("wiki_2026.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for label in [u"冬", u"春", u"夏", u"秋"]:
        print(u"\n=== %s季 %d 部 ===" % (label, len(res[label])))
        for it in res[label]:
            print(u"  " + it["zh"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
