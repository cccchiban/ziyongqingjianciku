"""从 iPlant（植物智）分类树递归抓取中国植物的中文名、学名。

流程：
  1. /info/<拉丁名> 取页面内 spno（分类树节点 id）
  2. POST /ashx/getsublist.ashx?type=sublist&spid=<spno> 取下级（分页，每页 20）
  3. 逐层下探到种
节点缓存写入 data/raw/<kind>/<spid>.json，可断点续跑。
本机代理会显著拖慢请求，故 trust_env=False 直连并复用连接。
"""
import json
import os
import re
import sys
import threading
import time
import urllib.parse
from queue import Queue

import requests
from requests.adapters import HTTPAdapter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlantNameTableBot/1.0"
WORKERS = 8
_local = threading.local()


def sess():
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.trust_env = False
        s.headers.update({"User-Agent": UA})
        ad = HTTPAdapter(pool_connections=4, pool_maxsize=4)
        s.mount("https://", ad)
        _local.s = s
    return s


def http(url, post=False, tries=4):
    for i in range(tries):
        try:
            r = sess().post(url, timeout=60) if post else sess().get(url, timeout=60)
            if r.status_code == 404:
                return ""
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(1 + 2 * i)
    return ""


def sublist(spid, page=None, total=None):
    u = "https://www.iplant.cn/ashx/getsublist.ashx?type=sublist&spid=%s" % spid
    if page:
        u += "&page=%d&total=%d" % (page, total)
    txt = http(u, post=True)
    if not txt.strip():
        return [], 0
    try:
        d = json.loads(txt)
    except ValueError:
        return [], 0
    return d.get("list") or [], int(d.get("total") or 0)


def spno_of(latin):
    h = http("https://www.iplant.cn/info/" + urllib.parse.quote(latin))
    m = re.search(r'var spno = "(\d+)"', h)
    if not m:
        return None, ""
    cn = re.search(r'var spcname = "([^"]*)"', h)
    return m.group(1), (cn.group(1) if cn else "")


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def load(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except ValueError:
            return None
    return None


def level_of(latin):
    t = latin.replace("×", " ").split()
    if len(t) >= 2 and re.fullmatch(r"[a-z\-]+", t[1]):
        return "infra" if len(t) >= 3 and t[2].rstrip(".") in ("var", "subsp", "f", "forma", "subvar") else "species"
    return "genus"


def children_of(spid, kind, stats):
    path = os.path.join(RAW, kind, "%s.json" % spid)
    cached = load(path)
    if cached is not None:
        return cached["children"]
    stats["node"] += 1
    first, total = sublist(spid)
    children = list(first)
    for p in range(2, total + 1):
        lst, _ = sublist(spid, p, total)
        children.extend(lst)
    save(path, {"children": children, "total": total})
    return children


def crawl(kind, entry):
    sp, cn = spno_of(entry)
    if not sp:
        print("入口失败", entry, flush=True)
        return []
    print("入口", entry, sp, cn, flush=True)
    stats = {"node": 0}
    q = Queue()
    q.put((sp, cn, entry, "root"))
    out = []
    lock = threading.Lock()
    t0 = time.time()

    def worker():
        while True:
            item = q.get()
            if item is None:
                return
            spid, cname, latin, level = item
            try:
                if level in ("species", "infra"):
                    with lock:
                        out.append((cname, latin, level))
                else:
                    for c in children_of(spid, kind, stats):
                        n = (c.get("cname") or "").strip()
                        la = (c.get("latin2") or "").strip()
                        if n and la:
                            q.put((str(c.get("cid")), n, la, level_of(la)))
            except Exception as e:
                print("ERR", spid, cname, e, flush=True)
            finally:
                q.task_done()

    ths = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    for t in ths:
        t.start()
    q.join()
    for _ in ths:
        q.put(None)
    rows = sorted(set(out))
    save(os.path.join(DATA, "%s_species.json" % kind), rows)
    print(kind, "物种", len(rows), "节点", stats["node"], "%.0fs" % (time.time() - t0), flush=True)
    return rows


def crawl_spid(kind, spid, cname=""):
    print("入口 spid", spid, cname, flush=True)
    stats = {"node": 0}
    q = Queue()
    q.put((spid, cname, spid, "root"))
    out = []
    lock = threading.Lock()
    t0 = time.time()

    def worker():
        while True:
            item = q.get()
            if item is None:
                return
            sid, cn, latin, level = item
            try:
                if level in ("species", "infra"):
                    with lock:
                        out.append((cn, latin, level))
                else:
                    for c in children_of(sid, kind, stats):
                        n = (c.get("cname") or "").strip()
                        la = (c.get("latin2") or "").strip()
                        if n and la:
                            q.put((str(c.get("cid")), n, la, level_of(la)))
            except Exception as e:
                print("ERR", sid, cn, e, flush=True)
            finally:
                q.task_done()

    ths = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    for t in ths:
        t.start()
    q.join()
    for _ in ths:
        q.put(None)
    rows = sorted(set(out))
    save(os.path.join(DATA, "%s_species.json" % kind), rows)
    print(kind, "物种", len(rows), "节点", stats["node"], "%.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "--spid":
        crawl_spid(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    else:
        crawl(sys.argv[1], sys.argv[2])
