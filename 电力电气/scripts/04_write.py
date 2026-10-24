"""写出 电力电气.tsv 与 词库列表.md。"""
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
    "电力设备企业名录": "1415 条全是公司名",
    "电力线路": "455 条地域线路名（阿产线、包一线）",
    "我QJ的工作": "个人工作范围内的变电站名",
    "锡电标准化": "供电分局名与个人姓名",
    "by": "检修部门名",
    "发电设备管理": "故障描述句（齿轮油泵损坏、叶轮松动）",
    "柜体盘厂用名词": "厂内工艺术语与个人姓名混排",
    "骆驼蓄电池": "企业车间用语与品牌名",
    "TFT-LCD工艺": "面板厂工艺术语，非电力",
    "装饰工程": "人名为首的工程报价词",
    "断路器的选择": "整库为安装说明句",
    "车载电力工程学": "整库 3 条句子",
    "行业专业术语": "含饲料添加剂等跨领域词",
    "电话通信": "呼叫中心系统配置词",
}


def main():
    rows = json.load(open(WORK / "rows.json", encoding="utf-8"))
    assert len(rows) > 1000, "词条数异常，拒绝覆盖：%d" % len(rows)
    tsv = OUT / "电力电气词库.tsv"
    lines = ["%s\t%s\t%d" % (r["w"], r["py"], r["freq"]) for r in rows]
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("写入", tsv.name, len(rows), "条")

    meta = json.load(open(WORK / "meta.json", encoding="utf-8"))
    md = ["# 搜狗词库·电力电气分类", "",
          "抓取自 https://pinyin.sogou.com/dict/cate/index/103 ，共 %d 个词库，"
          "原始词条 %d，去重并与既有词库判重后入库 %d 条。"
          % (len(meta), sum(m["words"] for m in meta), len(rows)),
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
    md.append("内容不是词条或与电力无关（%d 个）：" % len(corpus))
    md.append("")
    for m in corpus:
        md.append("- **%s**（%d 条）：%s" % (m["name"], m["words"], CORPUS[m["name"]]))
    md += ["", "企业或个人自建词库（%d 个）：" % len(corp), ""]
    md.append("、".join(m["name"] for m in corp) + "。")
    with open(OUT / "词库列表.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")
    print("写入 词库列表.md", len(meta), "个源词库")


if __name__ == "__main__":
    main()
