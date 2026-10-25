# -*- coding: utf-8 -*-
"""生成 英语/流行词/流行词汇词库.tsv。

来源：牛津、韦氏、柯林斯三家年度词汇官方页（含近年完整获奖名单与入围词）、
剑桥词典 2025 年新增词条公告（BBC 中文报道），以及公开的年度流行语盘点。
词面取英语圈真实流通的拼写，不收自造词与整句。

词面为纯拉丁字母（可含数字），拼音字段按仓库惯例逐字符空格分隔：
`meme -> m e m e`、`web3 -> w e b 3`，与 其他/互联网软件名称词库.tsv 的
`GitHub -> G i t H u b` 一致。

**只用单 token 词面**：仓库约束「词面不含空格」，故 goblin mode、aura farming、
touch grass 这类真双词短语一律不收，只收英语圈已普遍连写的合体形式
（ragebait、brainrot、vibecoding、tradwife）。这一取舍写在 AGENT.md。

判重只做本库内部去重，不与既有词库判重——跨库重复留到并入 综合词库.qj
时按词面统一处理（同中国神话库、英语文学词库的做法）。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "流行词"))
TARGET = os.path.join(OUT, "流行词汇词库.tsv")

TOKEN = re.compile(r"^[A-Za-z0-9]+$")

GROUPS = [
    ("社交媒体缩写", 900, """
lol omg btw tbh idk imo ngl fyi aka asap bff tmi nsfw irl nvm tbf icymi
dm idc ttyl brb afk
"""),
    ("网络流行语", 885, """
meme vibe cringe flex hype stan ghosting situationship doomscrolling
gaslighting mansplaining humblebrag clapback influencer unfollow selfie
hashtag viral trending clickbait catfish doxxing trolling spam
vlogger livestream podcast binge bloopers spoiler cancelled
facepalm fomo yolo
"""),
    ("Z 世代与 Alpha 世代俚语", 870, """
skibidi sigma gyatt rizz delulu mogging looksmaxxing fanumtax ohio mid
based cap nocap bet slay bussin banger glazing bruh goat lit yeet
ghosted simp stanning ratio copium hopium
"""),
    ("年度词汇", 865, """
vax brainrot slop ragebait vibecoding brat permacrisis lockdown youthquake
omnishambles
"""),
    ("AI 与科技流行词", 860, """
chatbot prompt hallucination agentic biohack deepfake algorithm metadata
blockchain crypto metaverse tokenomics web3 dataset fintech
algorithmic generative multimodal
"""),
    ("职场与生活新词", 845, """
quietquitting rageapplying mousejiggler workwife workspouse broligarchy
tradwife beigeflag hustle sidehustle burnout
"""),
    ("生活方式流行词", 840, """
hygge lagom bromance staycation glamping gastropub foodie brunch superfood
detox mindfulness wellness selfcare minimalism workaholic
"""),
    ("口语感叹与应答", 850, """
yikes oops meh yay ugh nope yep aww ew huh nah yeah
"""),
]


def main():
    rows, problems = [], []
    owner = {}
    for group, base, blob in GROUPS:
        for i, w in enumerate(blob.split()):
            if len(w) < 2:
                problems.append(("单字词", w)); continue
            if not TOKEN.match(w):
                problems.append(("非纯拉丁字母数字词面", w)); continue
            if w.lower() in owner:
                problems.append(("库内重复", "%s 已在 %s" % (w, owner[w.lower()])))
                continue
            py = " ".join(w)
            if len(py.split(" ")) != len(w):
                problems.append(("音节点数不符", "%s %s" % (w, py))); continue
            owner[w.lower()] = group
            freq = max(base - min(i // 5, 7) * 10, base - 70)
            rows.append((w, py, freq))

    if problems:
        print("异常 %d 条：" % len(problems))
        for p in problems:
            print("  %s: %s" % p)
        return 1
    if not rows:
        print("词条为 0，拒绝写出", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: (-r[2], r[1], r[0]))
    os.makedirs(OUT, exist_ok=True)
    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
        for w, py, fr in rows:
            fh.write("%s\t%s\t%d\n" % (w, py, fr))
    print("写出 %s：%d 条，词频 %d—%d"
          % (os.path.basename(TARGET), len(rows),
             min(r[2] for r in rows), max(r[2] for r in rows)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
