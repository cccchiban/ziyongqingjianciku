"""校验 动漫词库.tsv：格式、词面唯一、音节数、词频、排序、编码。"""
import pathlib
import re
import sys

TSV = pathlib.Path(__file__).parent.parent / u"动漫词库.tsv"
CJK = re.compile(u"^[\\u3400-\\u9fff]+$")
SYL = re.compile(u"^[a-z]+[1-5]$")
PYL = re.compile(u"^[a-z1-5 ]+$")


def main():
    raw = TSV.read_bytes()
    fails = []
    if not raw.endswith(b"\n"):
        fails.append(u"末行缺换行")
    if b"\r\n" in raw:
        fails.append(u"存在 CRLF 行尾")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(u"非 UTF-8：%s" % e)
        return 1

    rows = []
    for i, line in enumerate(text.split("\n"), 1):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            fails.append(u"第 %d 行字段数 %d" % (i, len(parts)))
            continue
        rows.append((i, parts[0], parts[1], parts[2]))

    seen = {}
    dup = []
    for i, w, py, fq in rows:
        if w in seen:
            dup.append((w, seen[w], i))
        seen[w] = i
        if not w or " " in w or "\u3000" in w:
            fails.append(u"第 %d 行词面含空格：%r" % (i, w))
        if not CJK.match(w):
            fails.append(u"第 %d 行词面非纯汉字：%r" % (i, w))
        if len(w) < 2:
            fails.append(u"第 %d 行单字词面：%r" % (i, w))
        syl = py.split(" ")
        if len(syl) != len(w):
            fails.append(u"第 %d 行音节数 %d != 字数 %d：%s" % (i, len(syl), len(w), w))
        if not PYL.match(py):
            fails.append(u"第 %d 行拼音非法字符：%r" % (i, py))
        for s in syl:
            if not SYL.match(s):
                fails.append(u"第 %d 行音节缺声调：%r（%s）" % (i, s, w))
        if not fq.isdigit() or int(fq) <= 0:
            fails.append(u"第 %d 行词频非正整数：%r" % (i, fq))
        if "ü" in py or "lue" in py.split(" ") or "nue" in py.split(" "):
            fails.append(u"第 %d 行 ü 未写 v：%r" % (i, py))

    for w, a, b in dup[:10]:
        fails.append(u"词面重复：%s（第 %d 与 %d 行）" % (w, a, b))

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
    print(u"重复词面 %d，字节 %d，末行换行 %s"
          % (len(dup), len(raw), raw.endswith(b"\n")))

    if fails:
        print(u"\n失败 %d 项（前 25）：" % len(fails))
        for f in fails[:25]:
            print("  " + f)
        return 1
    print(u"\n全部通过：三字段真 Tab、词面唯一且纯汉字、符号数=字数、"
          u"拼音全带声调、ü 写 v、词频正整数、排序符合「词频降序→拼音→词面」、"
          u"UTF-8 + LF、末行换行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
