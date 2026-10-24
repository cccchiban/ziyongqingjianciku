import gzip, json, re, time, urllib.request

BASE = "https://pinyin.sogou.com/dict/cate/index/118"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=30)
            data = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            return data.decode("utf-8", "ignore")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


BLOCK = re.compile(r'<div class="dict_detail_block[^"]*">(.*?)<div class="dict_dl_btn">', re.S)


def parse(html):
    out = []
    for m in BLOCK.finditer(html):
        b = m.group(1)
        idm = re.search(r"/dict/detail/index/(\d+)", b)
        namem = re.search(r"/dict/detail/index/\d+'>([^<]+)</a>", b)
        dl = re.search(r'id=(\d+)&name=([^"&]*)', m.group(0))
        cnt = re.findall(r'<div class="show_title">下载次数：</div>\s*<div class="show_content">(\d+)</div>', b)
        upd = re.findall(r'<div class="show_title">更新时间：</div>\s*<div class="show_content">([\d\-: ]+)</div>', b)
        if not (idm and namem):
            continue
        out.append({
            "id": int(idm.group(1)),
            "name": namem.group(1).strip(),
            "downloads": int(cnt[0]) if cnt else 0,
            "updated": upd[0].strip() if upd else "",
        })
    return out


def main():
    seen = {}
    page = 1
    while page <= 30:
        url = BASE + ("" if page == 1 else "/default/%d" % page)
        items = parse(get(url))
        if not items:
            break
        for it in items:
            seen.setdefault(it["id"], it)
        print("page %d: %d items, total %d" % (page, len(items), len(seen)), flush=True)
        page += 1
        time.sleep(1.0)
    rows = list(seen.values())
    with open("dicts.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("total", len(rows))


if __name__ == "__main__":
    main()
