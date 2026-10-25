"""枚举搜狗「动漫」分类（cate/index/404）的 297 个词库，写出 dicts.json。"""
import gzip
import json
import pathlib
import re
import time
import urllib.request

BASE = "https://pinyin.sogou.com/dict/cate/index/404"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
WORK.mkdir(parents=True, exist_ok=True)

BLOCK = re.compile(r'<div class="dict_detail_block[^"]*">(.*?)<div class="dict_dl_btn">', re.S)
TOTAL = re.compile(r'共有\s*(\d+)\s*个词库')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=30)
            data = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            return data.decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("%s: %s" % (url, last))


def parse(html):
    """按 dict_detail_block 分块解析：整页正则会把侧栏推荐一并截进来。"""
    out = []
    for m in BLOCK.finditer(html):
        block = m.group(1)
        idm = re.search(r"/dict/detail/index/(\d+)", block)
        namem = re.search(r"/dict/detail/index/\d+'>([^<]+)</a>", block)
        dl = re.search(r'id=(\d+)&name=([^"&]*)', m.group(0))
        cnt = re.findall(r'<div class="show_title">下载次数：</div>\s*'
                         r'<div class="show_content">(\d+)</div>', block)
        upd = re.findall(r'<div class="show_title">更新时间：</div>\s*'
                         r'<div class="show_content">([\d\-: ]+)</div>', block)
        samples = re.search(r'<div class="show_title">词条样例：</div>\s*'
                            r'<div class="show_content">(.*?)</div>', block, re.S)
        if not (idm and namem):
            continue
        out.append({
            "id": int(idm.group(1)),
            "name": namem.group(1).strip(),
            "downloads": int(cnt[0]) if cnt else 0,
            "updated": upd[0].strip() if upd else "",
            "samples": samples.group(1).strip() if samples else "",
            "dl": ("https://pinyin.sogou.com/d/dict/download_cell.php?id=%s&name=%s"
                   % (dl.group(1), dl.group(2))) if dl else "",
        })
    return out


def main():
    seen = {}
    declared = None
    empty_streak = 0
    for page in range(1, 41):
        url = BASE + ("" if page == 1 else "/default/%d" % page)
        html = get(url)
        if declared is None:
            m = TOTAL.search(html)
            declared = int(m.group(1)) if m else None
        items = parse(html)
        new = 0
        for it in items:
            if it["id"] not in seen:
                seen[it["id"]] = it
                new += 1
        print("page %2d: %2d items, +%2d new, total %3d" % (page, len(items), new, len(seen)),
              flush=True)
        empty_streak = empty_streak + 1 if (not items or new == 0) else 0
        if empty_streak >= 2:
            print("连续两页无新增，停止翻页", flush=True)
            break
        time.sleep(1.0)
    rows = list(seen.values())
    json.dump(rows, open(WORK / "dicts.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("声明 %s 个，抓到 %d 个" % (declared, len(rows)))
    if declared is not None and len(rows) != declared:
        print("!! 数量与页面声明不一致，需排查")


if __name__ == "__main__":
    main()
