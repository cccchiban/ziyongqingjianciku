"""写出 动漫词库.tsv 与 词库列表.md。"""
import json
import pathlib
import sys
from importlib import util

WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
OUT = pathlib.Path(__file__).parent.parent

spec = util.spec_from_file_location("m3", str(pathlib.Path(__file__).parent / "03_merge.py"))
m3 = util.module_from_spec(spec)
spec.loader.exec_module(m3)
EXCLUDE_NAMES = m3.EXCLUDE_NAMES

# 整库排除原因
CORPUS = {
    u"勤务词语2025套装": u"政治军事勤务术语，与动漫无关",
    u"tk1": u"教学设计与教育学理论术语，与动漫无关",
    u"彩红天堂": u"聊天句与个人签名（我的皮肤最美丽）",
    u"亚梦吧": u"贴吧个人介绍句（喜欢绿色讨厌红色）",
}


def main():
    rows = json.load(open(WORK / "rows.json", encoding="utf-8"))
    assert len(rows) > 10000, u"词条数异常，拒绝覆盖：%d" % len(rows)
    lines = ["%s\t%s\t%d" % (r["w"], r["py"], r["freq"]) for r in rows]
    with open(OUT / u"动漫词库.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(u"写入 动漫词库.tsv %d 条" % len(rows))

    meta = json.load(open(WORK / "meta.json", encoding="utf-8"))
    raw = sum(m["words"] for m in meta)
    md = [u"# 搜狗词库·动漫分类", "",
          u"抓取自 https://pinyin.sogou.com/dict/cate/index/404 ，共 %d 个词库，"
          u"原始词条 %d，去重并与既有源词库判重后入库 %d 条。"
          % (len(meta), raw, len(rows)),
          "",
          u"| # | 词库 | 词条 | 下载量 | 更新时间 |",
          u"| ---: | --- | ---: | ---: | --- |"]
    for i, m in enumerate(sorted(meta, key=lambda m: -m["words"]), 1):
        note = CORPUS.get(m["name"])
        name = m["name"] + (u"（未收录：%s）" % note if note else "")
        md.append("| %d | %s | %d | %d | %s |"
                  % (i, name, m["words"], m["downloads"], m["updated"]))
    md += ["", u"## 未收录的源词库", ""]
    for n, why in CORPUS.items():
        m = next((x for x in meta if x["name"] == n), None)
        if m:
            md.append(u"- **%s**（%d 条）：%s" % (n, m["words"], why))
    with open(OUT / u"词库列表.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    print(u"写入 词库列表.md %d 个源词库" % len(meta))


if __name__ == "__main__":
    main()
