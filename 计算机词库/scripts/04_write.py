"""写出 计算机词库.tsv 与 词库列表.md。"""
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

# 未收录原因：语料/话术/工单为整库不成词，其余是企业或个人自建词库
CORPUS = {
    "项目经理案头手册": "书中句子片段，非词条",
    "360电脑专家话术": "客服话术问句",
    "机场专业用词": "空管通话用语，与计算机无关",
    "蚂蚁云客服-花呗云": "客服话术",
    "铁塔电信运维故障工单专用词汇": "故障工单描述句",
    "角色t83": "提示词写作指令句",
    "百度术语词条（文学类）": "百科字段名（作者是、连载于）",
    "牛皮癣标题": "标题党模板句",
    "焙烧煤矸石、": "建材化验词",
    "协会": "公司名与个人词条",
    "甘肃小青年": "客服工单话术",
    "行测": "公务员考试词，与计算机无关",
    "会计考试用": "会计考试词，与计算机无关",
}


def main():
    rows = json.load(open(WORK / "rows.json", encoding="utf-8"))
    assert len(rows) > 1000, "词条数异常，拒绝覆盖：%d" % len(rows)
    tsv = OUT / "计算机词库.tsv"
    lines = ["%s\t%s\t%d" % (r["w"], r["py"], r["freq"]) for r in rows]
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("写入", tsv.name, len(rows), "条")

    meta = json.load(open(WORK / "meta.json", encoding="utf-8"))
    md = ["# 搜狗词库·计算机分类", "",
          "抓取自 https://pinyin.sogou.com/dict/cate/index/97 ，共 233 个词库，"
          "原始词条 %d，去重并与既有词库判重后入库 %d 条。" % (sum(m["words"] for m in meta), len(rows)),
          "",
          "| # | 词库 | 词条 | 下载量 | 更新时间 |",
          "| ---: | --- | ---: | ---: | --- |"]
    for i, m in enumerate(meta, 1):
        note = None
        if m["name"] in EXCLUDE_NAMES:
            note = CORPUS.get(m["name"]) or "企业或个人自建词库"
        name = m["name"] + ("（未收录：%s）" % note if note else "")
        md.append("| %d | %s | %d | %d | %s |" % (i, name, m["words"], m["downloads"], m["updated"]))
    md += ["", "## 未收录的源词库", ""]
    corpus = [m for m in meta if m["name"] in CORPUS]
    corp = [m for m in meta if m["name"] in EXCLUDE_NAMES and m["name"] not in CORPUS]
    md.append("内容不是词条或与计算机无关（%d 个）：" % len(corpus))
    md.append("")
    for m in corpus:
        md.append("- **%s**（%d 条）：%s" % (m["name"], m["words"], CORPUS[m["name"]]))
    md += ["", "企业或个人自建词库（%d 个），内容为公司名、人名、产品名与口号：" % len(corp), ""]
    md.append("、".join(m["name"] for m in corp) + "。")
    with open(OUT / "词库列表.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    print("写入 词库列表.md", len(meta), "个源词库")


if __name__ == "__main__":
    main()
