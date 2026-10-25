# -*- coding: utf-8 -*-
"""由分源统计生成 常用词/常用词.tsv（词\t拼音\t词频）。"""
import os, sys, csv, json, re, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WARD = os.path.dirname(ROOT)
STATS = os.path.join(ROOT, "stats")
OUT = os.path.join(WARD, "常用词.tsv")
DICT_TXT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                        ".omnicrawl", ".agent_tmp", "files", "_libs",
                        "jieba-0.42.1", "jieba", "dict.txt")

from pypinyin import lazy_pinyin, Style

DOMAINS = {
    "bilibili_comments": ("talk", 1.0),
    "danmaku": ("talk", 1.0),
    "weibo_senti_100k": ("social", 1.0),
    "weibo_comments_v1": ("social", 0.9),
    "online_shopping_10_cats": ("shop", 1.0),
    "waimai_10k": ("shop", 0.7),
}

TOP_N = 20000
FREQ_HI, FREQ_LO = 1000, 200
MIN_RATE = 1.5e-5
MAX_RATE = 0.30
DOMAIN_BONUS = 1.0

STOP = set("""
这个 那个 什么 怎么 这样 那样 这么 那么 这些 那些 这里 那里 哪里 哪些 这种 那种
一个 一些 一样 一直 一下 一点 一起 一定 一般 一边 一次 一件 一条 一天 一切
我们 你们 他们 她们 它们 咱们 大家 自己 别人 人家
就是 不是 但是 可是 还是 只是 也是 都是 于是 而是 并且 或者 虽然 不过 因为 所以
如果 而且 然而 然后 因此 否则 不然 要不 要么 要是 这就 那是 这是 还会 还能
可以 可能 应该 需要 必须 能够 不能 不会 不要 不用 不行 不少 不断 不管 不仅
知道 觉得 认为 感觉 希望 想要 打算 准备 开始 继续 结束 完成
已经 正在 曾经 刚刚 刚才 现在 当时 以后 以前 之后 之前 之间 之中 其中
真的 确实 其实 当然 好像 似乎 也许 大概 差不多 几乎 简直 实在 的确
有点 有些 很多 多少 几个 两个 三个 每个 整个 全部 所有 任何 其他
出来 起来 上来 下来 过来 回来 进去 出去 回去 过去 得到 收到 找到
看看 想想 说说 试试 走走 听听 讲讲 问问 用了 看了 说了 做了 想了
的话 时候 东西 事情 问题 地方 方面 情况 意思 意义 方式 方法
什么样 为什么 是不是 有没有 能不能 会不会 要不要 怎么样 怎么办
哈哈 哈哈哈 哈哈哈哈 呵呵 嘿嘿 嘻嘻 呜呜 啊啊 啊啊啊 哇哇 哎呀 哎呦 哦哦 嗯嗯
不了 不到 不好 不如 不想 不像 不少 不能 不会 不要 不用 不行 不过 不断
""".split())

AFFIX_ONLY = set("""
不 没 很 太 更 最 都 也 就 还 又 才 再 却 并 且 或 及 与 和 的 了 着 过 吗 呢 吧 啊 呀 哦 嘛 啦
""".split())

# 短语残片：以虚词/指示词开头，或整条由「程度副词 + 形容词」构成，都不是独立词目
FRAG_HEAD = ("这么", "那么", "怎样", "比较", "从此", "就是", "也就是", "不能", "不要", "不会",
             "不管", "非常", "特别", "有点", "一些", "一个", "一样", "一直", "已经", "应该",
             "可以", "还是", "不是", "只是", "什么", "怎么", "这个", "那个", "这种", "那种",
             "再", "绝不", "根本", "仅仅", "整一", "从今", "需要", "怎样才能", "哪有什么")

CJK = re.compile(r"^[\u3400-\u9fff]+$")

# 读音修正：pypinyin 对「地」作状语助词、「得」作补语助词一律给本调
DE_PARTICLE_WORDS = set("""
快乐地 慢慢地 默默地 认真地 好好地 开心地 静静地 轻轻地 努力地 用力地 大声地 小声地
飞快地 迅速地 悄悄地 偷偷地 紧紧地 深深地 远远地 高高地 好好地 轻轻地
跑得快 说得好 做得好 长得好 干得漂亮 干得好 唱得好 打得好 玩得好
""".split())

TONE_FIX = {
    "好处": "hao3 chu5", "关系": "guan1 xi5", "答应": "da1 ying5",
    "多少": "duo1 shao5", "认识": "ren4 shi5", "知识": "zhi1 shi5",
    # 「子」作实义语素读本调 zi3，作名词后缀读轻声 zi5
    "电子": "dian4 zi3", "原子": "yuan2 zi3", "分子": "fen4 zi3",
    "离子": "li2 zi3", "因子": "yin1 zi3", "棋子": "qi2 zi3",
    "双子": "shuang1 zi3", "西门子": "xi1 men2 zi3",
    "电子竞技": "dian4 zi3 jing4 ji4", "电子商务": "dian4 zi3 shang1 wu4",
    # 长度义的「长」读 chang2
    "加长": "jia1 chang2", "超长": "chao1 chang2", "变长": "bian4 chang2",
    # 「重」表「再一次」读 chong2
    "重装": "chong2 zhuang1", "重装系统": "chong2 zhuang1 xi4 tong3",
    "重发": "chong2 fa1", "重构": "chong2 gou4", "重启": "chong2 qi3",
    "重置": "chong2 zhi4", "重做": "chong2 zuo4", "重来": "chong2 lai2",
    "重建": "chong2 jian4", "重修": "chong2 xiu1", "重开": "chong2 kai1",
    # 其余逐条核定
    "发帖": "fa1 tie3", "微调": "wei1 tiao2", "老子": "lao3 zi3",
    "知识产权": "zhi1 shi5 chan3 quan2", "电子商务": "dian4 zi3 shang1 wu4",
    "干饭": "gan4 fan4", "妖精": "yao1 jing5",
}


def load_dict_words():
    words = set()
    with open(DICT_TXT, encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if p:
                words.add(p[0])
    return words


def load_source(name):
    p = os.path.join(STATS, "src_%s.csv" % name)
    if not os.path.exists(p):
        return {}
    d = {}
    with open(p, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        next(r)
        for w, df, tf in r:
            d[w] = (int(df), int(tf))
    return d


def pinyin_of(word):
    if word in TONE_FIX:
        return TONE_FIX[word]
    py = lazy_pinyin(word, style=Style.TONE3, neutral_tone_with_five=True,
                     errors=lambda x: [""] * len(x))
    if word in DE_PARTICLE_WORDS and py[-1] in ("di4", "de2"):
        py[-1] = "de5"
    return " ".join(py)


def is_fragment(word):
    for h in FRAG_HEAD:
        if word.startswith(h) and len(word) > len(h):
            return True
    return False


def main():
    with open(os.path.join(STATS, "stats_meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    per_source = meta["per_source"]

    dictwords = load_dict_words()
    tables = {}
    for name in DOMAINS:
        if name in per_source:
            t = load_source(name)
            if t:
                tables[name] = t

    score, total_df, domains = {}, {}, {}
    for name, table in tables.items():
        domain, weight = DOMAINS[name]
        docs = per_source[name]["docs"]
        if not docs:
            continue
        for w, (df, tf) in table.items():
            if w in STOP or w in AFFIX_ONLY or is_fragment(w):
                continue
            if len(w) < 2 or not CJK.match(w):
                continue
            rate = df / docs
            if rate < MIN_RATE or rate > MAX_RATE:
                continue
            score[w] = score.get(w, 0.0) + weight * math.log10(1 + rate / MIN_RATE)
            total_df[w] = total_df.get(w, 0) + df
            domains.setdefault(w, set()).add(domain)

    cand = []
    for w, s in score.items():
        if w not in dictwords:
            continue
        hits = sum(1 for n in tables if w in tables[n])
        if hits < 2:
            continue
        cand.append((w, s + DOMAIN_BONUS * (len(domains[w]) - 1), total_df[w]))

    if not cand:
        raise SystemExit("没有候选词，拒绝写出空库")

    cand.sort(key=lambda x: (-x[1], -x[2], x[0]))
    cand = cand[:TOP_N]

    hi, lo = cand[0][1], cand[-1][1]
    out = []
    for w, s, d in cand:
        py = pinyin_of(w)
        parts = py.split(" ")
        if len(parts) != len(w) or any(not p for p in parts):
            continue
        freq = FREQ_LO + (FREQ_HI - FREQ_LO) * (s - lo) / max(hi - lo, 1e-9)
        out.append((w, py, int(round(freq))))

    seen, final = set(), []
    for w, py, fq in sorted(out, key=lambda x: (-x[2], x[0])):
        if w in seen:
            continue
        seen.add(w)
        final.append((w, py, fq))
    final.sort(key=lambda x: (-x[2], x[1], x[0]))

    if not final:
        raise SystemExit("过滤后为空，拒绝写出空库")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for w, py, fq in final:
            f.write("%s\t%s\t%d\n" % (w, py, fq))

    print("写出 %s：%d 条，词频 %d—%d" % (OUT, len(final), final[-1][2], final[0][2]))
    for w, py, fq in final[:40]:
        print("   %-10s %-26s %d" % (w, py, fq))
    print("...")
    for w, py, fq in final[-8:]:
        print("   %-10s %-26s %d" % (w, py, fq))


if __name__ == "__main__":
    main()
