"""由 综合词库.tsv 生成 Rime 词典 综合词库.dict.yaml：编码去声调，权重为源词频。"""
import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TSV = ROOT / "综合词库.tsv"
OUT = ROOT / "综合词库.dict.yaml"

HEADER = """# Rime dictionary
# encoding: utf-8
#
# 由 综合词库.tsv 转换：编码为源拼音去声调，权重为源词频，词面未改动。
# 单独挂载：把 schema 的 translator/dictionary 指向本文件；
# 与 rime_ice 合用时在 rime_ice.dict.yaml 的 import_tables 里按权重顺序追加本词典。
#
---
name: 综合词库
version: "1.0"
sort: by_weight
...
"""


def main():
    lines = []
    skipped = []
    with io.open(TSV, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 3:
                continue
            w, py, fr = p
            # '/' 不是 Rime 的拼写分隔符；'#' 开头会被当成注释整行吞掉
            if "/" in py or w.startswith("#"):
                skipped.append(w)
                continue
            code = " ".join(s.rstrip("012345") for s in py.split(" "))
            lines.append("%s\t%s\t%s" % (w, code, fr))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER)
        f.write("\n".join(lines) + "\n")
    print("写出 %s，词条 %d，剔除 %d %s" % (OUT.name, len(lines), len(skipped), skipped))


if __name__ == "__main__":
    main()
