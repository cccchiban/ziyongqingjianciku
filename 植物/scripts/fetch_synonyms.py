"""抓取 iPlant 种级页面的「俗名」区块，汇总写入 data/syn_bulk.tsv。

断点续跑：已抓过的学名跳过。返回 HTML 过短或解析不出 infomore 结构时重试，
仍失败则记为空（视为该页无俗名），不静默丢弃。
输出列：中文名 \\t 学名 \\t 俗名（顿号分隔）
"""
import json
import os
import re
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlantNameTableBot/1.0"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "syn_bulk.tsv")

_lock = threading.Lock()
STATS = {"done": 0, "has": 0, "none": 0, "fail": 0}
SYN = re.compile(r"<div>俗名：(.*?)</div>", re.S)
TAG = re.compile(r"<[^>]+>")


def parse(h):
    """返回 (页面是否有效, 俗名列表)。"""
    if not h or len(h) < 5000:
        return False, []
    m = SYN.search(h)
    if not m:
        return True, []
    body = m.group(1)
    items = re.findall(r"<a[^>]*>(.*?)</a>", body, re.S) or re.split(r"[、，,]", TAG.sub("", body))
    out = []
    for a in items:
        a = re.sub(r"[\s\u3000\xa0]+", "", TAG.sub("", a)).strip("、，,。；;")
        if a and a not in out:
            out.append(a)
    return True, out


def fetch(url):
    """每次独立会话：长连接复用会让本站返回不含 infomore 的残缺页面。"""
    s = requests.Session()
    s.trust_env = False
    try:
        r = s.get(url, timeout=60, headers={"User-Agent": UA})
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""
    finally:
        s.close()


def one(row):
    cname, latin = row[0], row[1]
    for _ in range(3):
        h = fetch("https://www.iplant.cn/info/" + urllib.parse.quote(latin))
        ok, syn = parse(h)
        if ok:
            break
        time.sleep(2)
    else:
        with _lock:
            STATS["fail"] += 1
        return "%s\t%s\t%s\n" % (cname, latin, "")
    with _lock:
        STATS["done"] += 1
        STATS["has" if syn else "none"] += 1
        if STATS["done"] % 2000 == 0:
            print("进度 %d 有俗名 %d 无 %d 失败 %d" % (
                STATS["done"], STATS["has"], STATS["none"], STATS["fail"]), flush=True)
    return "%s\t%s\t%s\n" % (cname, latin, "、".join(syn))


def main(src):
    rows = []
    with open(src, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0] and p[1]:
                rows.append((p[0], p[1]))

    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) == 3:
                    done.add(p[1])
    todo = [r for r in rows if r[1] not in done]
    print("待抓 %d 已完成 %d" % (len(todo), len(done)), flush=True)

    t0 = time.time()
    buf = []
    with open(OUT, "a", encoding="utf-8", newline="\n") as out, ThreadPoolExecutor(max_workers=6) as ex:
        for line in ex.map(one, todo):
            buf.append(line)
            if len(buf) >= 500:
                out.write("".join(buf))
                out.flush()
                buf = []
        out.write("".join(buf))
    print("完成 %d 有俗名 %d 无 %d 失败 %d  %.0fs" % (
        STATS["done"], STATS["has"], STATS["none"], STATS["fail"], time.time() - t0), flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, "tasks.tsv"))
