import json, pathlib, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scel import parse_scel

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
REFERER = "https://pinyin.sogou.com/dict/cate/index/104"
DL = "https://pinyin.sogou.com/d/dict/download_cell.php?id=%d&name=%s"
WORK = pathlib.Path(__file__).parent.parent / ".omnicrawl_work"
SCEL = WORK / "scel"
SCEL.mkdir(parents=True, exist_ok=True)


def fetch(r):
    cache = SCEL / ("%d.scel" % r["id"])
    if cache.exists() and cache.stat().st_size > 1024:
        return r["id"], cache.read_bytes()
    url = DL % (r["id"], urllib.parse.quote(r["name"]))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": REFERER})
    last = None
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(req, timeout=60).read()
            if not data.startswith(b"@\x15\x00\x00DCS") and not data.startswith(b"@\x15\x00\x00VCS"):
                raise ValueError("not scel %r" % data[:16])
            cache.write_bytes(data)
            return r["id"], data
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("%s: %s" % (r["name"], last))


def main():
    rows = json.load(open(WORK / "dicts.json", encoding="utf-8"))
    result = {}
    errors = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch, r): r for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            r = futs[f]
            try:
                did, data = f.result()
                result[did] = len(data)
            except Exception as e:
                errors.append(str(e))
                print("FAIL", e, flush=True)
            if i % 10 == 0:
                print("progress %d/%d" % (i, len(rows)), flush=True)
    meta = []
    for r in rows:
        p = SCEL / ("%d.scel" % r["id"])
        ok = p.exists() and p.stat().st_size > 1024
        words, aligned = 0, False
        if ok:
            try:
                ws, end, total = parse_scel(p.read_bytes())
                words, aligned = len(ws), end == total
            except Exception as e:
                print("PARSE FAIL", r["name"], e, flush=True)
        meta.append({"id": r["id"], "name": r["name"], "downloads": r["downloads"],
                     "updated": r["updated"], "size": p.stat().st_size if ok else 0,
                     "words": words, "aligned": aligned})
    json.dump(meta, open(WORK / "meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("dicts", len(meta), "ok", sum(1 for m in meta if m["size"]), "words", sum(m["words"] for m in meta))
    print("misaligned", [m["name"] for m in meta if m["size"] and not m["aligned"]])
    print("missing", [m["name"] for m in meta if not m["size"]])
    print("errors", errors[:5])


if __name__ == "__main__":
    main()
