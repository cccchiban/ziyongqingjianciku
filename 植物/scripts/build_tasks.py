"""从分类树缓存（data/raw/<kind>/<spid>.json）还原「中文名 \\t 学名 \\t spno」清单。

父节点文件里 children 每项含 cid/cname/latin2，cid 即该节点自身的 spno。
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw")


def join_sci(latin, sub):
    """父节点拉丁名不完整（只到属）时，用子节点自己的拉丁名。"""
    return sub


def main():
    rows = {}
    for kind in sorted(os.listdir(RAW)):
        d = os.path.join(RAW, kind)
        if not os.path.isdir(d) or kind == "syn":
            continue
        for f in glob.glob(os.path.join(d, "*.json")):
            try:
                obj = json.load(open(f, encoding="utf-8"))
            except ValueError:
                continue
            for c in obj.get("children") or []:
                cid = str(c.get("cid") or "").strip()
                cn = (c.get("cname") or "").strip()
                la = (c.get("latin2") or "").strip()
                if not cid or not cn or not la:
                    continue
                rows.setdefault(cid, (cn, la, cid))
    out = os.path.join(DATA, "tasks.tsv")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for cid in sorted(rows, key=lambda x: int(x) if x.isdigit() else 0):
            cn, la, cid = rows[cid]
            f.write("%s\t%s\t%s\n" % (cn, la, cid))
    print("任务", len(rows), "->", out)


if __name__ == "__main__":
    main()
