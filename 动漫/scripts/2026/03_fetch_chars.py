# -*- coding: utf-8 -*-
"""批量抓取 2026 新番的维基条目，缓存纯文本供角色名抽取。

逻辑与 `../2025/03_fetch_chars.py` 一致：维基条目名不含季别括注，
故先用规范化后的主名尝试，再退回原始全名。并行 12 线程。
缓存目录 .omnicrawl_work/char_raw/（与 2025 共用，文件名按 md5 不冲突）。
"""
import gzip
import hashlib
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
RAW = WORK / "char_raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Accept-Language": "zh-CN,zh;q=0.9"})
    try:
        r = urllib.request.urlopen(req, timeout=15)
        d = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            d = gzip.decompress(d)
        return d.decode("utf-8", "ignore")
    except Exception:
        return None


def plain(html):
    html = re.sub(u"(?is)<(script|style|sup)[^>]*>.*?</\\1>", " ", html)
    html = re.sub(u"(?s)<br\\s*/?>", u"\n", html)
    html = re.sub(u"(?s)</(p|div|li|tr|h[1-6]|dd|dt)>", u"\n", html)
    html = re.sub(u"(?s)<[^>]+>", u" ", html)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&times;", "×")]:
        html = html.replace(a, b)
    return re.sub(u"[ \\t\\u00a0]+", " ", html)


def candidates(src, mains):
    out = []
    for m in mains:
        if m and m != src and m not in out:
            out.append(m)
    if src not in out:
        out.append(src)
    return out


def work(item):
    title, mains = item
    key = hashlib.md5(title.encode("utf-8")).hexdigest()[:16]
    cache = RAW / (key + ".txt")
    if cache.exists() and cache.stat().st_size > 1024:
        return "hit", title
    for cand in candidates(title, mains):
        if len(cand) < 2:
            continue
        url = "https://zh.wikipedia.org/zh-hans/" + urllib.parse.quote(
            cand.replace(" ", "_"))
        html = get(url)
        if html and u"维基百科" in html:
            cache.write_text(plain(html), encoding="utf-8")
            return "ok", title
    cache.write_text("", encoding="utf-8")
    return "miss", title


def main():
    names = json.load(open(WORK / "names_2026.json", encoding="utf-8"))
    srcs, seen = [], set()
    for q in [u"冬", u"春", u"夏", u"秋"]:
        for r in names[q]:
            if r["src"] not in seen:
                seen.add(r["src"])
                srcs.append((r["src"], [x["w"] for x in names[q]
                                       if x["src"] == r["src"]]))
    print(u"待抓 %d 个作品" % len(srcs))

    ok = miss = hit = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(work, it): it for it in srcs}
        for n, f in enumerate(as_completed(futs), 1):
            st, title = f.result()
            if st == "ok":
                ok += 1
            elif st == "hit":
                hit += 1
            else:
                miss += 1
                if miss <= 40:
                    print(u"  失败 %s" % title, flush=True)
            if n % 25 == 0:
                print(u"  进度 %d/%d（新抓 %d，缓存 %d，失败 %d）"
                      % (n, len(srcs), ok, hit, miss), flush=True)
    print(u"完成：新抓 %d，已有缓存 %d，失败 %d" % (ok, hit, miss))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
