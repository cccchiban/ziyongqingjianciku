# -*- coding: utf-8 -*-
"""校验 动漫/更新.tsv（2025 + 2026 合并后）。"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
TSV = HERE.parent.parent / u"更新.tsv"

CJK = re.compile(u"[\\u3400-\\u9fff]")
NON_SYL = re.compile(u"[^\\u3400-\\u9fff]")
SYL = re.compile(u"^[a-z]+[1-5]$")

# 与 05_gen_update.py 保持一致：人工核定读音的词条，音节数不受汉字数约束
WORD_FIX = {
    u"乱马1/2": "luan4 ma3 er4 fen1 zhi1 yi1",
}

# 与 05_gen_update.py 的 digits_to_han 保持一致：词面里的数字按其汉语读法占音节，
# `从0位` 读 cong2 ling2 wei4，`100个` 读 yi1 bai3 ge4。
DIGIT = {u"0": u"零", u"1": u"一", u"2": u"二", u"3": u"三", u"4": u"四",
         u"5": u"五", u"6": u"六", u"7": u"七", u"8": u"八", u"9": u"九"}


def digits_to_han(word):
    def rep(m):
        s = m.group(0)
        if s == u"0":
            return u"零"
        n = int(s)
        if n < 10:
            return DIGIT[s]
        if n < 20:
            return u"十" + (DIGIT[str(n % 10)] if n % 10 else u"")
        if n < 100:
            return DIGIT[str(n // 10)] + u"十" + (DIGIT[str(n % 10)] if n % 10 else u"")
        if n < 1000:
            h, r = divmod(n, 100)
            out = DIGIT[str(h)] + u"百"
            if r == 0:
                return out
            if r < 10:
                return out + u"零" + DIGIT[str(r)]
            t, u_ = divmod(r, 10)
            return out + DIGIT[str(t)] + u"十" + (DIGIT[str(u_)] if u_ else u"")
        return u"".join(DIGIT[c] for c in s)
    return re.sub(u"[0-9]+", rep, word)


def main():
    raw = TSV.read_bytes()
    fails = []
    if not raw.endswith(b"\n"):
        fails.append(u"末行缺换行")
    if b"\r" in raw:
        fails.append(u"存在 CRLF")
    text = raw.decode("utf-8")

    rows, seen, dup = [], {}, []
    for i, line in enumerate(text.split("\n"), 1):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            fails.append(u"第 %d 行字段数 %d" % (i, len(parts)))
            continue
        w, py, fq = parts
        rows.append((i, w, py, fq))
        if w in seen:
            dup.append((w, seen[w], i))
        seen[w] = i
        if not CJK.search(w):
            fails.append(u"第 %d 行词面无汉字：%r" % (i, w))
        if len(w) < 2:
            fails.append(u"第 %d 行词面过短：%r" % (i, w))
        if len(w) > 24:
            fails.append(u"第 %d 行词面过长 %d：%s" % (i, len(w), w))
        han = NON_SYL.sub("", digits_to_han(w))
        syl = py.split(" ")
        # WORD_FIX 里的词条读音由人工核定，音节数与数字展开后的汉字数可能不等
        # （`乱马1/2` 读 luan4 ma3 er4 fen1 zhi1 yi1，是 8 音节对 5 汉字）
        if w not in WORD_FIX and len(syl) != len(han):
            fails.append(u"第 %d 行音节 %d != 汉字 %d：%s" % (i, len(syl), len(han), w))
        for s in syl:
            if not SYL.match(s):
                fails.append(u"第 %d 行音节非法 %r（%s）" % (i, s, w))
        if u"ü" in py:
            fails.append(u"第 %d 行 ü 未写 v：%r" % (i, py))
        if not fq.isdigit() or int(fq) <= 0:
            fails.append(u"第 %d 行词频非法：%r" % (i, fq))
        if int(fq) > 1000:
            fails.append(u"第 %d 行词频超 1000：%r" % (i, fq))

    for w, a, b in dup[:10]:
        fails.append(u"词面重复：%s（%d 与 %d 行）" % (w, a, b))

    prev = None
    for i, w, py, fq in rows:
        key = (-int(fq), py, w)
        if prev is not None and key < prev:
            fails.append(u"第 %d 行排序错误：%s" % (i, w))
            break
        prev = key

    freqs = [int(r[3]) for r in rows]
    print(u"行数 %d，词面唯一 %d，词频 %d—%d，档位 %d"
          % (len(rows), len(seen), min(freqs), max(freqs), len(set(freqs))))
    print(u"重复 %d，字节 %d，末行换行 %s"
          % (len(dup), len(raw), raw.endswith(b"\n")))

    if fails:
        print(u"\n失败 %d 项（前 20）：" % len(fails))
        for f in fails[:20]:
            print("  " + f)
        return 1
    print(u"\n全部通过。")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
