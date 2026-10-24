"""写出 通信与无线电词库.tsv 与 词库列表.md。"""
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

CORPUS = {
    "上海站名XX": "44815 条上海小区与站点名（阿波罗大厦、爱博二村地下车库）",
    "通信代维运营商-伍": "6 条工单事件描述（客服报障、合同物业纠纷）",
}


def main():
    rows = json.load(open(WORK / "rows.json", encoding="utf-8"))
    assert len(rows) > 200, "词条数异常，拒绝覆盖：%d" % len(rows)
    tsv = OUT / "通信与无线电词库.tsv"
    lines = ["%s\t%s\t%d" % (r["w"], r["py"], r["freq"]) for r in rows]
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("写入", tsv.name, len(rows), "条")

    meta = json.load(open(WORK / "meta.json", encoding="utf-8"))
    md = ["# 搜狗词库·通信与无线电分类", "",
          "抓取自 https://pinyin.sogou.com/dict/cate/index/118 ，共 %d 个词库，"
          "原始词条 %d，去重并与既有词库判重后入库 %d 条。"
          % (len(meta), sum(m["words"] for m in meta), len(rows)),
          "",
          "| # | 词库 | 词条 | 下载量 | 更新时间 |",
          "| ---: | --- | ---: | ---: | --- |"]
    for i, m in enumerate(meta, 1):
        note = CORPUS.get(m["name"])
        name = m["name"] + ("（未收录：%s）" % note if note else "")
        md.append("| %d | %s | %d | %d | %s |" % (i, name, m["words"], m["downloads"], m["updated"]))
    md += ["", "## 未收录的源词库", ""]
    for m in meta:
        if m["name"] in CORPUS:
            md.append("- **%s**（%d 条）：%s" % (m["name"], m["words"], CORPUS[m["name"]]))
    md += ["", "本分类 16 个词库中 `上海站名XX` 一家占 97% 词条且与通信无关，"
              "排除后实际可用的通信术语来源只有 15 个库。"]
    with open(OUT / "词库列表.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    print("写入 词库列表.md", len(meta), "个源词库")


if __name__ == "__main__":
    main()
