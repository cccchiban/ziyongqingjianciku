"""合并分类树名录与俗名抓取结果，生成 植物/植物.tsv：中文名 \\t 学名 \\t 俗名。

俗名多个以「、」分隔，无则 `-`；只保留与中文名不同、纯汉字、2—8 字的俗名，同一条最多 8 个，短名优先。
"""
import glob
import io
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw")
SYN = os.path.join(RAW, "syn")
OUT = os.path.abspath(os.path.join(HERE, "..", "植物.tsv"))

HZ = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0003ffff]+$")

STOP_SUB = (
    "生活", "栖息", "分布", "主要", "属于", "位于", "广泛", "是指", "包括", "常见",
    "一种", "一类", "某些", "少数", "其他", "等等", "以上", "以下", "附近", "一带",
    "地区", "各省", "各地", "全国", "我国", "产于", "原产", "又称", "别名", "别称",
    "俗称", "学名", "中文名", "拉丁", "种加词", "变种", "亚种", "变型", "品种",
)
# 单字俗名只放行确实会单独敲的果蔬名
SINGLE_OK = {"橙", "梨", "柚", "桃", "李", "杏", "梅", "枣", "柿", "栗", "榛", "橙"}

STOP_EXACT = {
    "俗名", "别名", "别称", "学名", "又名", "又称", "俗称", "通称", "其他", "等等",
    "一种", "未知", "无名", "不详", "待定", "中国", "日本", "美洲", "欧洲", "亚洲",
    "非洲", "植物", "树木", "花草", "本种", "该种", "此种", "同上",
}


def clean(a, cname):
    a = re.sub(r"[\s\u3000\xa0]+", "", a)
    a = a.strip("、，,。；;：:'\"（）()《》【】[]")
    if not a or a == cname:
        return None
    if not HZ.fullmatch(a):
        return None
    if len(a) < 2:
        if a not in SINGLE_OK:
            return None
    elif len(a) > 8:
        return None
    if a in STOP_EXACT:
        return None
    for s in STOP_SUB:
        if s in a:
            return None
    return a


def load_json(f):
    try:
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError):
        return None


def load_manual():
    """人工核定俗名表：正名 	 俗名（顿号分隔），优先级高于抓取结果。"""
    d = {}
    for fn in ("manual_aliases.tsv", "manual_extra.tsv"):
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) != 2:
                    continue
                d.setdefault(parts[0], [])
                for a in parts[1].split("、"):
                    a = a.strip()
                    if a and a != parts[0] and a not in d[parts[0]]:
                        d[parts[0]].append(a)
    return d


def main():
    # 1) 分类树：中文名 -> 学名集合
    names = {}
    for kind in os.listdir(RAW):
        if kind == "syn":
            continue
        for f in glob.glob(os.path.join(RAW, kind, "*.json")):
            obj = load_json(f)
            if not obj:
                continue
            for c in obj.get("children") or []:
                cn = (c.get("cname") or "").strip()
                la = (c.get("latin2") or "").strip()
                if cn and la and HZ.fullmatch(cn):
                    names.setdefault(cn, set()).add(la)

    # 2) 俗名：学名 -> 俗名列表
    syns = {}
    stat = Counter()
    with io.open(os.path.join(DATA, "syn_bulk.tsv"), encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 3:
                continue
            stat["syn_total"] += 1
            if not p[2]:
                stat["空俗名或无区块"] += 1
                continue
            stat["有俗名"] += 1
            syns.setdefault(p[1], p[2].split("、"))

    # 补录：分类树未收录、但 iPlant 有条目的栽培植物（学名取自条目页面）
    extra = {}
    ep = os.path.join(DATA, "extra_plants.json")
    if os.path.exists(ep):
        for e in json.load(io.open(ep, encoding="utf-8")):
            extra[e["cname"]] = (e["latin"], e.get("syns") or [])

    manual = load_manual()
    for cn, (la, _) in extra.items():
        names.setdefault(cn, set()).add(la)

    rows = []
    for cn in sorted(names):
        latins = sorted(names[cn])
        got = []
        for la in latins:
            for a in syns.get(la, []):
                a = clean(a, cn)
                if a and a not in got:
                    got.append(a)
        for raw in extra.get(cn, (None, []))[1]:
            for part in re.split(r"[、，,；;]", raw):
                a = clean(part, cn)
                if a and a not in got:
                    got.append(a)
        for a in manual.get(cn, []):
            a = clean(a, cn)
            if a and a not in got:
                got.append(a)
        man = []
        for a in (manual.get(cn) or []):
            a2 = clean(a, cn)
            if a2 and a2 in got:
                man.append(a2)
        rest = [a for a in got if a not in man]
        rest.sort(key=lambda a: (len(a) > 4, len(a), a))
        got = (man + rest)[:8]
        if got:
            stat["条目有俗名"] += 1
        stat["俗名词元"] += len(got)
        rows.append((cn, latins[0], "、".join(got) if got else "-"))

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("%s\t%s\t%s\n" % r)
    print("条目 %d  %s" % (len(rows), dict(stat)))
    print("输出", OUT)


if __name__ == "__main__":
    main()
