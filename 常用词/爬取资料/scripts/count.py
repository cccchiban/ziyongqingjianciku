# -*- coding: utf-8 -*-
"""统计爬取评论语料中的高频词：总表 + 各源分表（用于跨源覆盖度判据）。"""
import os, sys, csv, json, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "stats")
LIBS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                    ".omnicrawl", ".agent_tmp", "files", "_libs", "jieba-0.42.1")

sys.path.insert(0, LIBS)
import jieba

CJK = re.compile(r"^[\u3400-\u9fff]+$")
NOISE = re.compile(r"https?://\S+|@[^\s:：]{1,20}|#[^#]{0,30}#|\[[^\]]{1,10}\]")

MIN_LEN, MAX_LEN = 2, 4

SOURCES = [
    ("bilibili_comments", "bilibili_comments.csv", "csv", "message"),
    ("danmaku", "danmaku.parquet", "parquet", "text"),
    ("weibo_senti_100k", "weibo_senti_100k.csv", "csv", "review"),
    ("weibo_comments_v1", "weibo_comments_v1.parquet", "parquet", "text"),
    ("online_shopping_10_cats", "online_shopping_10_cats.csv", "csv", "review"),
    ("waimai_10k", "waimai_10k.csv", "csv", "review"),
]


def iter_texts(path, kind, field):
    if kind == "csv":
        with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                v = row.get(field)
                if v:
                    yield v
    else:
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(path)
        for batch in pf.iter_batches(batch_size=50000, columns=[field]):
            for v in batch.column(0).to_pylist():
                if v:
                    yield v


def main():
    os.makedirs(OUT, exist_ok=True)
    df, tf, per_source = {}, {}, {}
    total_docs = 0
    t0 = time.time()

    for name, fname, kind, field in SOURCES:
        path = os.path.join(RAW, fname)
        if not os.path.exists(path):
            print("跳过（缺文件）", name)
            continue
        n = 0
        local_df, local_tf = {}, {}
        for text in iter_texts(path, kind, field):
            t = NOISE.sub(" ", text)
            if not t.strip():
                continue
            n += 1
            seen = set()
            for w in jieba.cut(t, cut_all=False):
                w = w.strip()
                if not w or not CJK.match(w) or not (MIN_LEN <= len(w) <= MAX_LEN):
                    continue
                tf[w] = tf.get(w, 0) + 1
                local_tf[w] = local_tf.get(w, 0) + 1
                if w not in seen:
                    seen.add(w)
                    df[w] = df.get(w, 0) + 1
                    local_df[w] = local_df.get(w, 0) + 1
            if n % 500000 == 0:
                print("  %s %d 条 %.0fs" % (name, n, time.time() - t0))
        per_source[name] = {"docs": n, "vocab": len(local_df)}
        total_docs += n
        lp = os.path.join(OUT, "src_%s.csv" % name)
        with open(lp, "w", encoding="utf-8", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["word", "df", "tf"])
            for w, d in sorted(local_df.items(), key=lambda x: (-x[1], x[0])):
                wr.writerow([w, d, local_tf[w]])
        print("%-26s %8d 条  词表 %7d  %.0fs" % (name, n, len(local_df), time.time() - t0))

    rows = sorted(((w, d, tf[w]) for w, d in df.items()), key=lambda x: (-x[1], -x[2], x[0]))
    with open(os.path.join(OUT, "wordfreq.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["word", "df", "tf"])
        wr.writerows(rows)

    meta = {
        "total_docs": total_docs,
        "vocab": len(rows),
        "per_source": per_source,
        "min_len": MIN_LEN,
        "max_len": MAX_LEN,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(OUT, "stats_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("总文档 %d，词表 %d" % (total_docs, len(rows)))


if __name__ == "__main__":
    main()
