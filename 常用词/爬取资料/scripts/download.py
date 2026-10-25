# -*- coding: utf-8 -*-
"""从 HuggingFace 公开数据集下载评论语料（多连接分段下载）。"""
import os, sys, json, time, threading, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}
CONN = 16
SMALL = 8 * 1024 * 1024

SOURCES = [
    ("bilibili_comments", "Midsummra/bilibilicomment", "bilibili.csv", "B站评论（message 字段）"),
    ("weibo_senti_100k", "dirtycomputer/weibo_senti_100k", "weibo_senti_100k.csv", "微博评论"),
    ("online_shopping_10_cats", "dirtycomputer/online_shopping_10_cats", "online_shopping_10_cats.csv", "电商商品评论"),
    ("waimai_10k", "XiangPan/waimai_10k", "waimai_10k.csv", "外卖评价"),
    ("douban_movie_comments", "Leoooooops/douban_movie_comments", "new_data.json", "豆瓣影评短评"),
    ("bilibili_sharegpt", "theblackcat102/bilibili_comments_sharegpt", "train.jsonl", "B站评论对话集"),
]


def open_url(url, headers=None, timeout=90):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=timeout)


def remote_size(url):
    with open_url(url, timeout=60) as r:
        return int(r.headers.get("Content-Length") or 0)


def fetch_part(url, start, end, out, idx, lock, prog, attempts=4):
    tmp = "%s.part%d" % (out, idx)
    got = 0
    for _ in range(attempts):
        try:
            h = {"Range": "bytes=%d-%d" % (start + got, end)}
            with open_url(url, headers=h, timeout=240) as r:
                data = r.read()
            with open(tmp, "ab") as f:
                f.write(data)
            got += len(data)
            prog[idx] = got
            if got >= end - start + 1:
                return True
        except Exception:
            time.sleep(1.5)
    return got >= end - start + 1


def download(url, out, conn=CONN):
    size = remote_size(url)
    if os.path.exists(out) and os.path.getsize(out) == size and size > 0:
        print("  跳过（已完整 %d bytes）" % size)
        return out
    for f in os.listdir(os.path.dirname(out) or "."):
        if f.startswith(os.path.basename(out) + ".part"):
            os.remove(os.path.join(os.path.dirname(out) or ".", f))
    conn = min(conn, 4) if size < SMALL else conn
    if conn < 1:
        conn = 1
    chunk = size // conn + 1
    lock = threading.Lock()
    prog = [0] * conn
    done = [False] * conn

    def worker(i):
        s = i * chunk
        e = min((i + 1) * chunk, size) - 1
        done[i] = fetch_part(url, s, e, out, i, lock, prog)

    t0 = time.time()
    ths = [threading.Thread(target=worker, args=(i,)) for i in range(conn)]
    for t in ths:
        t.start()
    while any(t.is_alive() for t in ths):
        cur = sum(prog)
        el = max(time.time() - t0, .1)
        sys.stdout.write("\r  %.1f/%.1f MB  %.0f KB/s " % (cur / 1e6, size / 1e6, cur / 1024 / el))
        sys.stdout.flush()
        time.sleep(1)
    for t in ths:
        t.join()
    print()
    if not all(done):
        raise RuntimeError("分段下载未全部完成: %s" % url)
    with open(out, "wb") as f:
        for i in range(conn):
            p = "%s.part%d" % (out, i)
            with open(p, "rb") as pf:
                f.write(pf.read())
            os.remove(p)
    print("  完成 %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))
    return out


def main():
    os.makedirs(RAW, exist_ok=True)
    only = sys.argv[1:] 
    manifest = []
    for key, repo, fname, note in SOURCES:
        if only and key not in only:
            continue
        url = "https://huggingface.co/datasets/%s/resolve/main/%s" % (repo, fname)
        out = os.path.join(RAW, key + os.path.splitext(fname)[1])
        print("== %s  <-  %s" % (key, url))
        try:
            download(url, out)
            manifest.append({"key": key, "repo": repo, "file": fname, "url": url,
                             "note": note, "path": os.path.relpath(out, ROOT).replace("\\", "/"),
                             "bytes": os.path.getsize(out)})
        except Exception as e:
            print("  失败:", type(e).__name__, str(e)[:160])
    mf = os.path.join(RAW, "manifest.json")
    old = []
    if os.path.exists(mf):
        with open(mf, encoding="utf-8") as f:
            old = json.load(f)
    keys = {m["key"] for m in manifest}
    merged = [m for m in old if m["key"] not in keys] + manifest
    with open(mf, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print("清单写入", mf)


if __name__ == "__main__":
    main()
